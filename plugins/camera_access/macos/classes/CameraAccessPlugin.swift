import Cocoa
import FlutterMacOS
import AVFoundation
import Metal
import MetalKit
import CoreImage
import CoreMedia
import CoreGraphics
import ImageIO
import CoreServices

// Para compatibilidade entre diferentes versões do macOS
#if canImport(UniformTypeIdentifiers) && swift(>=5.3)
import UniformTypeIdentifiers
#endif

/// Estrutura para resolução da câmera
struct CameraResolution {
    let width: Int
    let height: Int
    
    init(width: Int, height: Int) {
        self.width = width
        self.height = height
    }
}

/// Estrutura para gerenciar os ajustes de imagem
struct ImageAdjustments {
    var brightness: Double = 0.0
    var contrast: Double = 0.0
    var saturation: Double = 0.0
    var sharpness: Double = 0.0
    var exposure: Double = 0.0
    var gain: Double = 1.0
    var filter: String? = nil
    var useHardwareAcceleration: Bool = true
    
    static let `default` = ImageAdjustments()
    
    init(
        brightness: Double = 0.0,
        contrast: Double = 0.0,
        saturation: Double = 0.0,
        sharpness: Double = 0.0,
        exposure: Double = 0.0,
        gain: Double = 1.0,
        filter: String? = nil,
        useHardwareAcceleration: Bool = true
    ) {
        self.brightness = brightness.clamped(to: -1.0...1.0)
        self.contrast = contrast.clamped(to: -1.0...1.0)
        self.saturation = saturation.clamped(to: -1.0...1.0)
        self.sharpness = sharpness.clamped(to: 0.0...1.0)
        self.exposure = exposure.clamped(to: -1.0...1.0)
        self.gain = gain.clamped(to: 0.0...2.0)
        self.filter = filter
        self.useHardwareAcceleration = useHardwareAcceleration
    }
    
    init?(from dict: [String: Any]?) {
        guard let dict = dict else { return nil }
        
        self.brightness = (dict["brightness"] as? Double ?? 0.0).clamped(to: -1.0...1.0)
        self.contrast = (dict["contrast"] as? Double ?? 0.0).clamped(to: -1.0...1.0)
        self.saturation = (dict["saturation"] as? Double ?? 0.0).clamped(to: -1.0...1.0)
        self.sharpness = (dict["sharpness"] as? Double ?? 0.0).clamped(to: 0.0...1.0)
        self.exposure = (dict["exposure"] as? Double ?? 0.0).clamped(to: -1.0...1.0)
        self.gain = (dict["gain"] as? Double ?? 1.0).clamped(to: 0.0...2.0)
        self.filter = dict["filter"] as? String
        self.useHardwareAcceleration = dict["useHardwareAcceleration"] as? Bool ?? true
    }
    
    init?(fromMap dict: [String: Any]) {
        self.init(from: dict)
    }
    
    func toDict() -> [String: Any] {
        var dict: [String: Any] = [
            "brightness": brightness,
            "contrast": contrast,
            "saturation": saturation,
            "sharpness": sharpness,
            "exposure": exposure,
            "gain": gain,
            "useHardwareAcceleration": useHardwareAcceleration
        ]
        
        if let filter = filter {
            dict["filter"] = filter
        }
        
        return dict
    }
}

/// Extensão para limitar números em intervalos
extension Comparable {
    func clamped(to limits: ClosedRange<Self>) -> Self {
        return min(max(self, limits.lowerBound), limits.upperBound)
    }
}

public class CameraAccessPlugin: NSObject, FlutterPlugin {
    // Gerenciamento de sessão AVFoundation
    private var session: AVCaptureSession?
    private var currentDevice: AVCaptureDevice?
    private var currentOutput: AVCaptureVideoDataOutput?
    private var currentConnection: AVCaptureConnection?
    
    // Gerenciamento de frames otimizado
    private var lastFrame: CVPixelBuffer?
    private let sessionQueue = DispatchQueue(label: "camera.session.queue", qos: .userInteractive)
    private let processingQueue = DispatchQueue(label: "camera.processing.queue", qos: .userInteractive)
    private var frameSemaphore = DispatchSemaphore(value: 1)
    private var pixelBufferPool: CVPixelBufferPool?
    
    // Pool de recursos
    private var metalDevice: MTLDevice?
    private var commandQueue: MTLCommandQueue?
    private var textureCache: CVMetalTextureCache?
    private var ciContext: CIContext?
    
    // Resolução
    private var currentResolution = CGSize(width: 640, height: 480)
    
    // Controle de taxa de frames
    private var lastCaptureTime = Date()
    private var frameRateThrottle: TimeInterval = 1.0 / 30.0  // 30 FPS default
    private var adaptiveQuality = true
    private var consecutiveSlowFrames = 0
    private let maxConsecutiveSlowFrames = 5
    
    // Ajustes de imagem atuais
    private var currentAdjustments = ImageAdjustments.default
    
    // Registro e métricas 
    private var totalFramesProcessed: UInt64 = 0
    private var droppedFrames: UInt64 = 0
    private var processingTimes = [TimeInterval]()
    private let maxProcessingTimesSamples = 30
    
    // Estado de inicialização da câmera
    private var _isCameraInitialized: Bool = false
    
    // Filtros para processamento de imagem
    private var ciFilter: CIFilter?

    // MARK: - Zoom Methods
    
    /// Nível de zoom atual. Mantido para melhor controle
    private var currentZoomLevel: CGFloat = 1.0

    // MARK: - Properties
    
    /// Nível mínimo de zoom
    private let minZoomLevel: CGFloat = 1.0
    
    /// Nível máximo de zoom
    private let maxZoomLevel: CGFloat = 5.0

    // MARK: - White Balance Methods
    
    private var currentWhiteBalanceMode: String = "auto"
    
    // Propriedades para simular balanço de branco via software
    private var softwareWhiteBalanceEnabled: Bool = false
    private var redGain: CGFloat = 1.0
    private var greenGain: CGFloat = 1.0
    private var blueGain: CGFloat = 1.0

    public static func register(with registrar: FlutterPluginRegistrar) {
        let channel = FlutterMethodChannel(name: "camera_access", binaryMessenger: registrar.messenger)
        let instance = CameraAccessPlugin()
        registrar.addMethodCallDelegate(instance, channel: channel)
    }

    override init() {
        super.init()
        initializeMetalResources()
    }

    deinit {
        // Limpar recursos
        cleanupMetalResources()
        releasePixelBufferPool()
        
        // Garantir que a sessão seja fechada
        if session?.isRunning == true {
            session?.stopRunning()
        }
    }

    // Inicialização dos recursos Metal para processamento GPU
    private func initializeMetalResources() {
        // Obter dispositivo Metal padrão
        metalDevice = MTLCreateSystemDefaultDevice()
        
        guard let device = metalDevice else {
            NSLog("Metal não está disponível neste dispositivo")
            return
        }
        
        // Criar fila de comandos
        commandQueue = device.makeCommandQueue()
        
        // Criar cache de texturas Metal
        var textureCache: CVMetalTextureCache?
        CVMetalTextureCacheCreate(kCFAllocatorDefault, nil, device, nil, &textureCache)
        self.textureCache = textureCache
        
        // Configurar contexto Core Image otimizado para Metal
        let options = [CIContextOption.workingColorSpace: NSNull(),
                      CIContextOption.outputColorSpace: NSNull(),
                      CIContextOption.useSoftwareRenderer: NSNumber(value: false)]
        
        ciContext = CIContext(mtlDevice: device, options: options)
        
        NSLog("Recursos Metal inicializados com sucesso")
    }
    
    // Limpeza dos recursos Metal
    private func cleanupMetalResources() {
        ciContext = nil
        textureCache = nil
        commandQueue = nil
        metalDevice = nil
    }
    
    // Criar um pool de pixel buffers para reutilização
    private func createPixelBufferPool(width: Int, height: Int) -> CVPixelBufferPool? {
        let pixelBufferAttributes: [String: Any] = [
            kCVPixelBufferWidthKey as String: width,
            kCVPixelBufferHeightKey as String: height,
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
            kCVPixelBufferIOSurfacePropertiesKey as String: [:],
            kCVPixelBufferMetalCompatibilityKey as String: true
        ]
        
        var pixelBufferPool: CVPixelBufferPool?
        let poolAttributes = [kCVPixelBufferPoolMinimumBufferCountKey as String: 3]
        
        let status = CVPixelBufferPoolCreate(kCFAllocatorDefault, poolAttributes as CFDictionary, pixelBufferAttributes as CFDictionary, &pixelBufferPool)
        
        guard status == kCVReturnSuccess, let pool = pixelBufferPool else {
            NSLog("Falha ao criar pool de pixel buffers: \(status)")
            return nil
        }
        
        // Pré-alocar alguns buffers
        var pixelBuffers = [CVPixelBuffer]()
        for _ in 0..<3 {
            var pixelBuffer: CVPixelBuffer?
            CVPixelBufferPoolCreatePixelBuffer(nil, pool, &pixelBuffer)
            if let pixelBuffer = pixelBuffer {
                pixelBuffers.append(pixelBuffer)
            }
        }
        
        // Descartamos os buffers pré-alocados e deixamos eles no pool
        pixelBuffers.removeAll()
        
        return pool
    }
    
    // Liberar recursos do pool de pixel buffers
    private func releasePixelBufferPool() {
        pixelBufferPool = nil
    }

    public func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
        switch call.method {
        case "getPlatformVersion":
            result("macOS " + ProcessInfo.processInfo.operatingSystemVersionString)
        
        case "checkPermission":
            checkCameraPermission { hasPermission in
                result(hasPermission)
            }
            
        case "requestPermission":
            requestCameraAccess { granted in
                result(granted)
            }
            
        case "getAvailableCameras":
            let cameras = self.getAvailableCameras()
            result(cameras)
            
        case "startCameraSession":
            guard let args = call.arguments as? [String: Any],
                  let cameraId = args["cameraId"] as? String else {
                result(FlutterError(code: "INVALID_ARGUMENT", 
                                   message: "ID da câmera inválido ou ausente", 
                                   details: nil))
                return
            }
            
            startCameraSession(cameraId: cameraId) { success, error in
                if success {
                    result(true)
                } else {
                    result(FlutterError(code: "CAMERA_ERROR", 
                                       message: error ?? "Falha ao iniciar sessão de câmera", 
                                       details: nil))
                }
            }
            
        case "startCameraSessionWithConfig":
            guard let args = call.arguments as? [String: Any],
                  let cameraId = args["cameraId"] as? String else {
                result(FlutterError(code: "INVALID_ARGUMENT", 
                                   message: "ID da câmera inválido ou ausente", 
                                   details: nil))
                return
            }
            
            // Extrair configurações opcionais
            var resolution: CameraResolution?
            if let resMap = args["resolution"] as? [String: Any],
               let width = resMap["width"] as? Int,
               let height = resMap["height"] as? Int {
                resolution = CameraResolution(width: width, height: height)
            }
            
            var adjustments: ImageAdjustments?
            if let adjMap = args["adjustments"] as? [String: Any] {
                adjustments = ImageAdjustments(fromMap: adjMap)
            }
            
            // Log para diagnóstico
            if let res = resolution {
                NSLog("📱 Iniciando sessão com resolução: \(res.width)x\(res.height)")
            }
            
            startCameraSessionWithConfig(cameraId: cameraId, resolution: resolution, adjustments: adjustments) { success, error in
                if success {
                    result(true)
                } else {
                    result(FlutterError(code: "CAMERA_ERROR", 
                                       message: error ?? "Falha ao iniciar sessão de câmera", 
                                       details: nil))
                }
            }
            
        case "stopCameraSession":
            stopCameraSession { success in
                result(success)
            }
            
        case "captureFrame":
            let forceCapture = (call.arguments as? [String: Any])?["forceCapture"] as? Bool ?? false
            
            // Log para diagnóstico
            
            captureCurrentFrame(forceCapture: forceCapture) { frameData, error in
                if let error = error {
                    result(FlutterError(code: "CAPTURE_ERROR", message: error, details: nil))
                    return
                }
                
                if let frameData = frameData {
                    // Log para diagnóstico
                    result(frameData)
                } else {
                    result(FlutterError(code: "CAPTURE_ERROR", message: "Nenhum frame capturado", details: nil))
                }
            }
            
        case "captureFrameAlternative":
            let highQuality = (call.arguments as? [String: Any])?["highQuality"] as? Bool ?? true
            
            captureFrameAlternative(highQuality: highQuality) { frameData in
                if let frameData = frameData {
                    result(FlutterStandardTypedData(bytes: frameData))
                } else {
                    result(FlutterError(code: "CAPTURE_ERROR", message: "Nenhum frame capturado", details: nil))
                }
            }
            
        case "getLastFrameFromBuffer":
            // Log para diagnóstico
            NSLog("🔍 Recuperando último frame do buffer")
            
            getLastFrameFromBuffer { frameData in
                if let frameData = frameData {
                    result(FlutterStandardTypedData(bytes: frameData))
                } else {
                    result(FlutterError(code: "BUFFER_ERROR", message: "Nenhum frame no buffer", details: nil))
                }
            }
            
        case "setResolution":
            guard let args = call.arguments as? [String: Any],
                  let width = args["width"] as? Int,
                  let height = args["height"] as? Int else {
                result(FlutterError(code: "INVALID_ARGS", message: "Argumentos inválidos", details: nil))
                return
            }
            setResolution(width: width, height: height, result: result)
        case "getCurrentResolution":
            getCurrentResolution(result: result)
        case "getAvailableResolutions":
            getAvailableResolutions(result: result)
        case "setImageAdjustments":
            if let args = call.arguments as? [String: Any],
               let brightness = args["brightness"] as? Double,
               let contrast = args["contrast"] as? Double,
               let exposure = args["exposure"] as? Double,
               let gain = args["gain"] as? Double {
                
                // Atualizar ajustes imediatamente
                currentAdjustments.brightness = CGFloat(brightness)
                currentAdjustments.contrast = CGFloat(contrast)
                currentAdjustments.exposure = CGFloat(exposure)
                currentAdjustments.gain = CGFloat(gain)
                
                // Opcionalmente definir outros parâmetros se fornecidos
                if let saturation = args["saturation"] as? Double {
                    currentAdjustments.saturation = CGFloat(saturation)
                }
                
                if let sharpness = args["sharpness"] as? Double {
                    currentAdjustments.sharpness = CGFloat(sharpness)
                }
                
                // Tratar explicitamente o caso onde o filtro é nulo
                if args.keys.contains("filter") {
                    if let filter = args["filter"] as? String {
                        currentAdjustments.filter = filter
                        NSLog("Filtro definido para: '\(filter)'")
                    } else {
                        // Se a chave 'filter' existe mas não é uma string, considerar como nulo (normal)
                        currentAdjustments.filter = nil
                        NSLog("Filtro definido como nulo (normal)")
                    }
                }
                
                if let useGPU = args["useHardwareAcceleration"] as? Bool {
                    currentAdjustments.useHardwareAcceleration = useGPU
                }
                
                // Atualizar filtros explicitamente para garantir que alterações sejam aplicadas
                updateImageFilters()
                
                // Confirmar sucesso
                result(true)
            } else {
                result(FlutterError(code: "INVALID_ARGUMENTS", 
                                  message: "Argumentos inválidos para setImageAdjustments", 
                                  details: nil))
            }
        case "getCurrentImageAdjustments":
            getCurrentImageAdjustments(result: result)
        
        // Métodos de zoom
        case "getZoomLevel":
            getZoomLevel(result: result)
        case "getMaxZoomLevel":
            getMaxZoomLevel(result: result)
        case "setZoomLevel":
            if let args = call.arguments as? [String: Any],
               let zoomLevel = args["zoomLevel"] as? Double {
                setZoomLevel(level: CGFloat(zoomLevel), result: result)
            } else {
                result(FlutterError(code: "INVALID_ARGUMENTS", 
                                  message: "Nível de zoom inválido ou ausente", 
                                  details: nil))
            }
            
        case "setWhiteBalance":
            if let args = call.arguments as? [String: Any],
               let mode = args["mode"] as? String {
                setWhiteBalance(mode: mode, result: result)
            } else {
                result(FlutterError(code: "INVALID_ARGUMENTS", 
                                  message: "Modo de balanço de branco inválido ou ausente", 
                                  details: nil))
            }
            
        default:
            result(FlutterMethodNotImplemented)
        }
    }

    // MARK: - Permission Methods

    private func checkCameraPermission(completion: @escaping (Bool) -> Void) {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            completion(true)
        default:
            completion(false)
        }
    }

    private func requestCameraAccess(completion: @escaping (Bool) -> Void) {
        AVCaptureDevice.requestAccess(for: .video) { granted in
            DispatchQueue.main.async {
                completion(granted)
            }
        }
    }

    // MARK: - Camera Methods

    private func getAvailableCameras() -> [[String: Any]] {
        var cameras: [[String: Any]] = []

        // Usar AVCaptureDeviceDiscoverySession em vez do método deprecado
        let discoverySession = AVCaptureDevice.DiscoverySession(
            deviceTypes: [.builtInWideAngleCamera, .externalUnknown],
            mediaType: .video,
            position: .unspecified
        )
        let devices = discoverySession.devices

        for device in devices {
            var position = "unknown"

            // Determinando posição com base em características
            if device.hasMediaType(.video) {
                // Tentativa de determinar se é frontal ou traseira - isso é difícil
                // em macOS mais antigo, então geralmente consideramos "unknown"

                // Verificar pelo nome se pode ser uma webcam integrada
                if device.localizedName.lowercased().contains("facetime") ||
                   device.localizedName.lowercased().contains("built-in") {
                    position = "front"
                } else if device.localizedName.lowercased().contains("usb") ||
                          device.localizedName.lowercased().contains("external") {
                    position = "external"
                }
            }

            let camera: [String: Any] = [
                "id": device.uniqueID,
                "name": device.localizedName,
                "isDefault": device == AVCaptureDevice.default(for: .video),
                "position": position
            ]

            cameras.append(camera)
        }

        return cameras
    }

    private func startCameraSessionWithConfig(
        cameraId: String,
        resolution: CameraResolution?,
        adjustments: ImageAdjustments?,
        completion: @escaping (Bool, String?) -> Void
    ) {
        // Configurar resolução se fornecida
        if let resolution = resolution {
            currentResolution = CGSize(width: resolution.width, height: resolution.height)
        }
        
        // Configurar ajustes se fornecidos
        if let adjustments = adjustments {
            currentAdjustments = adjustments
        }
        
        // Iniciar a sessão de câmera
        startCameraSession(cameraId: cameraId) { success, error in
            if success {
                completion(true, nil)
            } else {
                completion(false, error)
            }
        }
    }

    private func startCameraSession(cameraId: String, completion: @escaping (Bool, String?) -> Void) {
        // Verificar se já existe uma sessão e encerrá-la
        self.stopCameraSession { _ in
            // Crie uma nova sessão
            let session = AVCaptureSession()
            
            // Determinar preset baseado na resolução
            var sessionPreset: AVCaptureSession.Preset = .medium
            
            if self.currentResolution.width >= 1920 && self.currentResolution.height >= 1080 {
                // Full HD
                if session.canSetSessionPreset(.hd1920x1080) {
                    sessionPreset = .hd1920x1080
                    NSLog("Usando preset Full HD (1920x1080)")
                } else if session.canSetSessionPreset(.hd1280x720) {
                    // Fallback para HD se Full HD não for suportado
                    sessionPreset = .hd1280x720
                    NSLog("Full HD não suportado, usando HD (1280x720)")
                    self.currentResolution = CGSize(width: 1280, height: 720)
                }
            } else if self.currentResolution.width >= 1280 && self.currentResolution.height >= 720 {
                // HD
                if session.canSetSessionPreset(.hd1280x720) {
                    sessionPreset = .hd1280x720
                    NSLog("Usando preset HD (1280x720)")
                }
            } else if self.currentResolution.width >= 640 && self.currentResolution.height >= 480 {
                // VGA
                sessionPreset = .vga640x480
                NSLog("Usando preset VGA (640x480)")
            } else {
                // Para resoluções menores, usar low ou medium
                if self.currentResolution.width <= 320 && session.canSetSessionPreset(.low) {
                    sessionPreset = .low
                    NSLog("Usando preset low para resolução menor")
                } else {
                    sessionPreset = .medium
                    NSLog("Usando preset medium")
                }
            }
            
            session.sessionPreset = sessionPreset

            // Encontre o dispositivo solicitado usando DiscoverySession
            let discoverySession = AVCaptureDevice.DiscoverySession(
                deviceTypes: [.builtInWideAngleCamera, .externalUnknown],
                mediaType: .video,
                position: .unspecified
            )
            let devices = discoverySession.devices
            guard let device = devices.first(where: { $0.uniqueID == cameraId }) else {
                DispatchQueue.main.async {
                    completion(false, "Dispositivo de câmera não encontrado")
                }
                return
            }

            do {
                // Configure a entrada
                let input = try AVCaptureDeviceInput(device: device)
                if session.canAddInput(input) {
                    session.addInput(input)
                } else {
                    throw NSError(domain: "CameraAccess", code: 1, userInfo: [NSLocalizedDescriptionKey: "Não foi possível adicionar a entrada à sessão"])
                }
                
                // Verificar e selecionar o formato correto baseado na resolução
                self.configureOptimalFormat(for: device, with: self.currentResolution)
                
                // Configurar taxa de quadros e outros parâmetros
                try device.lockForConfiguration()
                
                // Definir uma taxa de quadros fixa para evitar problemas
                if device.activeFormat.videoSupportedFrameRateRanges.contains(where: { $0.maxFrameRate >= 30.0 }) {
                    NSLog("Câmera configurada para 30 FPS")
                    
                    // Usar valores exatos para duração do quadro
                    let frameDuration = CMTimeMake(value: 1, timescale: 30)
                    
                    // Aplicar somente se for compatível
                    if device.activeFormat.videoSupportedFrameRateRanges.contains(where: { 
                        CMTimeCompare($0.minFrameDuration, frameDuration) <= 0 && 
                        CMTimeCompare($0.maxFrameDuration, frameDuration) >= 0 
                    }) {
                        device.activeVideoMinFrameDuration = frameDuration
                        device.activeVideoMaxFrameDuration = frameDuration
                    }
                }
                
                // Ajustes de qualidade
                if device.isExposureModeSupported(.continuousAutoExposure) {
                    device.exposureMode = .continuousAutoExposure
                }
                
                if device.isWhiteBalanceModeSupported(.continuousAutoWhiteBalance) {
                    device.whiteBalanceMode = .continuousAutoWhiteBalance
                }
                
                // Configurar foco automático se suportado
                if device.isFocusModeSupported(.continuousAutoFocus) {
                    device.focusMode = .continuousAutoFocus
                }
                
                // Aplicar ajustes nativos se houver suporte
                self.applyNativeCameraAdjustments(device: device)
                
                device.unlockForConfiguration()

                // Configure a saída otimizada para melhor desempenho
                let output = AVCaptureVideoDataOutput()
                
                // Configurar formato de pixel otimizado para processamento GPU
                if self.currentAdjustments.useHardwareAcceleration {
                    output.videoSettings = [
                        (kCVPixelBufferPixelFormatTypeKey as String): kCVPixelFormatType_32BGRA,
                        (kCVPixelBufferMetalCompatibilityKey as String): true
                    ]
                } else {
                    output.videoSettings = [(kCVPixelBufferPixelFormatTypeKey as String): kCVPixelFormatType_32BGRA]
                }
                
                // Otimizar para velocidade vs qualidade
                output.setSampleBufferDelegate(self, queue: self.sessionQueue)
                output.alwaysDiscardsLateVideoFrames = true

                if session.canAddOutput(output) {
                    session.addOutput(output)
                } else {
                    throw NSError(domain: "CameraAccess", code: 2, userInfo: [NSLocalizedDescriptionKey: "Não foi possível adicionar a saída à sessão"])
                }

                // Configurar conexão de vídeo
                if let connection = output.connection(with: .video) {
                    self.currentConnection = connection
                    
                    // Configurar orientação - apenas portrait no macOS
                    connection.videoOrientation = .portrait
                    
                    // Nota: Estabilização de vídeo não está disponível no macOS
                    // As linhas relacionadas foram removidas
                }

                // Armazenar referências
                self.session = session
                self.currentDevice = device
                self.currentOutput = output
                
                // Configurar aceleração por hardware antes de iniciar a sessão
                self.setupHardwareAcceleration()
                
                // Configurar filtros de imagem
                self.updateImageFilters()

                // Iniciar a sessão em thread separado com alta prioridade
                DispatchQueue.global(qos: .userInitiated).async {
                    session.startRunning()
                    
                    DispatchQueue.main.async {
                        self._isCameraInitialized = true
                        completion(true, nil)
                    }
                }
            } catch {
                DispatchQueue.main.async {
                    self._isCameraInitialized = false
                    completion(false, "Erro ao configurar a câmera: \(error.localizedDescription)")
                }
            }
        }
    }

    /// Configura o formato de câmera mais próximo da resolução desejada
    private func configureOptimalFormat(for device: AVCaptureDevice, with targetResolution: CGSize) {
        let formats = device.formats
        var optimalFormat: AVCaptureDevice.Format?
        var optimalDimensions = CMVideoDimensions(width: 0, height: 0)
        var minDiff = Double.greatestFiniteMagnitude
        
        // Procurar o formato mais próximo da resolução desejada
        for format in formats {
            // Obter dimensões do formato
            let dimensions = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
            
            // Calcular diferença entre a resolução desejada e este formato
            let widthDiff = abs(Double(dimensions.width) - Double(targetResolution.width))
            let heightDiff = abs(Double(dimensions.height) - Double(targetResolution.height))
            let diff = widthDiff + heightDiff
            
            // Verificar se este formato é melhor que o anterior
            if diff < minDiff {
                minDiff = diff
                optimalFormat = format
                optimalDimensions = dimensions
            }
        }
        
        // Se encontramos um formato ideal, aplicá-lo
        if let format = optimalFormat {
            do {
                try device.lockForConfiguration()
                device.activeFormat = format
                
                // Atualizar resolução atual para a real que estamos usando
                self.currentResolution = CGSize(width: CGFloat(optimalDimensions.width), 
                                               height: CGFloat(optimalDimensions.height))
                
                NSLog("Formato configurado: \(optimalDimensions.width)x\(optimalDimensions.height)")
                
                device.unlockForConfiguration()
            } catch {
                NSLog("Erro ao configurar formato ideal: \(error.localizedDescription)")
            }
        }
    }

    /// Aplica os ajustes diretamente na câmera (quando possível)
    private func applyNativeCameraAdjustments(device: AVCaptureDevice) {
        do {
            try device.lockForConfiguration()
            defer { device.unlockForConfiguration() }
            
            // No macOS, as opções de ajuste nativo são mais limitadas
            // Ajuste de exposição básico
            if device.isExposureModeSupported(.continuousAutoExposure) {
                // Ajustar modo de exposição automática
                device.exposureMode = .continuousAutoExposure
            }
            
            // Ajuste de foco
            if device.isFocusModeSupported(.continuousAutoFocus) {
                device.focusMode = .continuousAutoFocus
            }
            
            // Ajuste de balanço de branco
            if device.isWhiteBalanceModeSupported(.continuousAutoWhiteBalance) {
                device.whiteBalanceMode = .continuousAutoWhiteBalance
            }
            
            // A maioria dos ajustes avançados (ISO, exposição personalizada, ganho)
            // serão aplicados via filtros de software, já que as APIs de ajuste de câmera
            // são mais limitadas no macOS em comparação com iOS
            
            NSLog("Ajustes nativos básicos aplicados; ajustes avançados serão aplicados via software")
            
        } catch {
            NSLog("Erro ao aplicar ajustes nativos: \(error.localizedDescription)")
        }
    }

    private func stopCameraSession(completion: @escaping (Bool) -> Void) {
        sessionQueue.async { [weak self] in
            guard let self = self else {
                DispatchQueue.main.async {
                    completion(false)
                }
                return
            }

            self.cleanupSession()

            DispatchQueue.main.async {
                self._isCameraInitialized = false
                completion(true)
            }
        }
    }

    private func cleanupSession() {
        if let session = self.session, session.isRunning {
            session.stopRunning()
        }

        self.session = nil
        self.currentDevice = nil
        self.currentOutput = nil
        self.currentConnection = nil
        self.lastFrame = nil
        self.ciFilter = nil
        
        // Limpar recursos de GPU
        self.commandQueue = nil
        self.textureCache = nil
        // Não é necessário limpar metalDevice ou ciContext, pois podem ser reutilizados
    }

    private func captureFrameWithAdjustments(
        forceCapture: Bool,
        adjustments: [String: Any]?,
        result: @escaping FlutterResult
    ) {
        processingQueue.async { [weak self] in
            guard let self = self else {
                DispatchQueue.main.async {
                    result(FlutterError(code: "SESSION_ERROR", message: "Instância do plugin inválida", details: nil))
                }
                return
            }
            
            // Verificar se a sessão está ativa
            guard let session = self.session, session.isRunning else {
                DispatchQueue.main.async {
                    result(FlutterError(code: "CAMERA_ERROR", message: "Sessão de câmera não está ativa", details: nil))
                }
                return
            }
            
            // Aguardar semáforo com timeout para evitar bloqueios
            guard self.frameSemaphore.wait(timeout: .now() + .milliseconds(forceCapture ? 50 : 5)) == .success else {
                DispatchQueue.main.async {
                    result(FlutterError(code: "TIMEOUT_ERROR", message: "Timeout ao aguardar acesso ao frame", details: nil))
                }
                return
            }
            
            // Liberar semáforo ao concluir
            defer { self.frameSemaphore.signal() }
            
            // Verificar se temos um frame válido
            guard let buffer = self.lastFrame else {
                DispatchQueue.main.async {
                    result(FlutterError(code: "CAMERA_ERROR", message: "Nenhum frame disponível da câmera", details: nil))
                }
                return
            }
            
            // Aplicar ajustes temporários se fornecidos
            let originalAdjustments = self.currentAdjustments
            if let adjustments = adjustments {
                self.currentAdjustments = ImageAdjustments(from: adjustments) ?? ImageAdjustments.default
            }
            
            do {
                // Início do timer para medir desempenho
                let startTime = CACurrentMediaTime()
                
                // Processar imagem com pipeline otimizado
                let imageData: Data
                
                if self.currentAdjustments.useHardwareAcceleration && self.metalDevice != nil {
                    // Usar implementação Metal
                    imageData = try self.processFrameWithMetal(buffer)
                } else {
                    // Fallback para CoreImage
                    imageData = try self.processFrameWithCoreImage(buffer)
                }
                
                // Restaurar ajustes originais
                self.currentAdjustments = originalAdjustments
                
                // Registrar tempo de processamento para ajuste adaptativo
                let processingTime = CACurrentMediaTime() - startTime
                self.trackProcessingTime(processingTime)
                
                if imageData.isEmpty {
                    DispatchQueue.main.async {
                        result(FlutterError(code: "CONVERSION_ERROR", message: "Dados de imagem vazios", details: nil))
                    }
                    return
                }
                
                DispatchQueue.main.async {
                    result(FlutterStandardTypedData(bytes: imageData))
                }
            } catch {
                // Restaurar ajustes originais em caso de erro
                self.currentAdjustments = originalAdjustments
                
                DispatchQueue.main.async {
                    result(FlutterError(code: "CONVERSION_ERROR", message: "Erro ao converter frame para imagem: \(error.localizedDescription)", details: nil))
                }
            }
        }
    }

    private func captureFrame(forceCapture: Bool, completion: @escaping (Any) -> Void) {
        if !_isCameraInitialized {
            completion(FlutterError(code: "CAMERA_UNAVAILABLE", 
                                  message: "Câmera não disponível",
                                  details: nil))
            return
        }
        
        // Verificar se temos um frame válido
        guard let pixelBuffer = lastFrame else {
            completion(FlutterError(code: "NO_FRAME", 
                                  message: "Nenhum frame disponível",
                                  details: nil))
            return
        }
        
        // Processar o frame
        do {
            let processedData = try processImageBuffer(pixelBuffer)
            completion(FlutterStandardTypedData(bytes: processedData))
        } catch {
            NSLog("❌ Erro ao processar frame: \(error.localizedDescription)")
            completion(FlutterError(code: "PROCESSING_ERROR", 
                                  message: "Erro ao processar frame: \(error.localizedDescription)",
                                  details: nil))
        }
    }

    // Método alternativo para captura de frame com configurações diferentes
    private func captureFrameAlternative(highQuality: Bool, completion: @escaping (Data?) -> Void) {
        sessionQueue.async { [weak self] in
            guard let self = self else {
                DispatchQueue.main.async {
                    completion(nil)
                }
                return
            }
            
            // Forçar a captura de um novo frame
            // Primeiro pausamos a sessão
            guard let session = self.session, session.isRunning else {
                DispatchQueue.main.async {
                    completion(nil)
                }
                return
            }
            
            session.stopRunning()
            
            // Esperamos um pouco
            Thread.sleep(forTimeInterval: 0.2)
            
            // Reiniciamos a sessão
            session.startRunning()
            
            // Esperamos um pouco mais para garantir que temos um novo frame
            Thread.sleep(forTimeInterval: 0.5)
            
            guard let buffer = self.lastFrame else {
                DispatchQueue.main.async {
                    completion(nil)
                }
                return
            }
            
            // Espera o semáforo para ter acesso exclusivo ao frame
            self.frameSemaphore.wait()
            
            do {
                // Usar alta qualidade na conversão
                let compressionFactor = highQuality ? 1.0 : 0.9
                let imageData = try self.processImageBuffer(buffer, compressionFactor: compressionFactor)
                
                // Libera o semáforo
                self.frameSemaphore.signal()
                
                if imageData.isEmpty {
                    DispatchQueue.main.async {
                        completion(nil)
                    }
                    return
                }
                
                NSLog("✅ Frame alternativo capturado: \(imageData.count) bytes")
                DispatchQueue.main.async {
                    completion(imageData)
                }
            } catch {
                // Libera o semáforo em caso de erro
                self.frameSemaphore.signal()
                
                DispatchQueue.main.async {
                    completion(nil)
                }
            }
        }
    }
    
    // Método para recuperar o último frame do buffer mesmo que pareça inválido
    private func getLastFrameFromBuffer(completion: @escaping (Data?) -> Void) {
        sessionQueue.async { [weak self] in
            guard let self = self else {
                DispatchQueue.main.async {
                    completion(nil)
                }
                return
            }
            
            // Tentar capturar diretamente da câmera, ignorando lastFrame
            guard let device = self.currentDevice else {
                DispatchQueue.main.async {
                    completion(nil)
                }
                return
            }
            
            // Tentar forçar um quadro fazendo ajuste na câmera
            do {
                try device.lockForConfiguration()
                
                // Ajustar foco para forçar atualização do frame
                if device.isFocusModeSupported(.autoFocus) {
                    device.focusMode = .autoFocus
                }
                
                // Ajustar exposição para forçar atualização
                if device.isExposureModeSupported(.autoExpose) {
                    device.exposureMode = .autoExpose
                }
                
                device.unlockForConfiguration()
                
                // Esperar um pouco para a câmera reagir
                Thread.sleep(forTimeInterval: 0.5)
                
                // Verificar se temos um frame
                guard let buffer = self.lastFrame else {
                    DispatchQueue.main.async {
                        completion(nil)
                    }
                    return
                }
                
                // Espera o semáforo
                self.frameSemaphore.wait()
                
                // Tentar converter o buffer com configurações de emergência
                let imageData = try self.processImageBuffer(buffer, compressionFactor: 1.0, emergency: true)
                
                // Libera o semáforo
                self.frameSemaphore.signal()
                
                NSLog("✅ Último frame recuperado: \(imageData.count) bytes")
                DispatchQueue.main.async {
                    completion(imageData)
                }
            } catch {
                if let buffer = self.lastFrame {
                    // Como último recurso, tentar extrair qualquer dado do buffer
                    self.frameSemaphore.wait()
                    
                    let width = CVPixelBufferGetWidth(buffer)
                    let height = CVPixelBufferGetHeight(buffer)
                    
                    // Criar e usar imagem vazia para casos de emergência
                    let emptyImage = NSImage(size: NSSize(width: width, height: height))
                    
                    if let tiffData = emptyImage.tiffRepresentation,
                       let bitmapRep = NSBitmapImageRep(data: tiffData),
                       let jpegData = bitmapRep.representation(using: .jpeg, properties: [:]) {
                        
                        self.frameSemaphore.signal()
                        
                        DispatchQueue.main.async {
                            completion(jpegData)
                        }
                    } else {
                        self.frameSemaphore.signal()
                        
                        DispatchQueue.main.async {
                            completion(nil)
                        }
                    }
                } else {
                    DispatchQueue.main.async {
                        completion(nil)
                    }
                }
            }
        }
    }

    // MARK: - New Resolution Methods
    
    private func setResolution(width: Int, height: Int, result: @escaping FlutterResult) {
        sessionQueue.async { [weak self] in
            guard let self = self else {
                DispatchQueue.main.async {
                    result(false)
                }
                return
            }
            
            // Verificar resolução válida
            guard width > 0 && height > 0 else {
                DispatchQueue.main.async {
                    result(false)
                }
                return
            }
            
            // Armazenar a nova resolução desejada
            self.currentResolution = CGSize(width: width, height: height)
            
            // Se tiver uma sessão ativa, tentar aplicar a nova resolução
            if let _ = self.session, let deviceId = self.currentDevice?.uniqueID {
                // Precisamos reiniciar a sessão para aplicar a nova resolução
                self.cleanupSession()
                
                // Reiniciar com a nova resolução
                self.startCameraSession(cameraId: deviceId) { success, error in
                    DispatchQueue.main.async {
                        if success {
                            result(true)
                        } else {
                            result(FlutterError(code: "CAMERA_ERROR", message: error ?? "Erro desconhecido", details: nil))
                        }
                    }
                }
            } else {
                // Se não há sessão ativa, apenas armazena a resolução para quando iniciar
                DispatchQueue.main.async {
                    result(true)
                }
            }
        }
    }
    
    private func getCurrentResolution(result: @escaping FlutterResult) {
        DispatchQueue.main.async {
            let resolutionMap: [String: Any] = [
                "width": Int(self.currentResolution.width),
                "height": Int(self.currentResolution.height)
            ]
            result(resolutionMap)
        }
    }
    
    private func getAvailableResolutions(result: @escaping FlutterResult) {
        sessionQueue.async { [weak self] in
            guard let self = self,
                  let device = self.currentDevice else {
                // Se não houver dispositivo, retornar resoluções padrão
                let defaultResolutions: [[String: Any]] = [
                    ["width": 640, "height": 480],
                    ["width": 1280, "height": 720],
                    ["width": 1920, "height": 1080]
                ]
                DispatchQueue.main.async {
                    result(defaultResolutions)
                }
                return
            }
            
            // Obter formatos suportados pelo dispositivo
            var availableResolutions: [[String: Any]] = []
            let formats = device.formats
            
            for format in formats {
                let dimensions = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
                let resolution: [String: Any] = [
                    "width": Int(dimensions.width),
                    "height": Int(dimensions.height)
                ]
                
                // Verificar se esta resolução já foi adicionada
                let alreadyAdded = availableResolutions.contains { existingRes in
                    return existingRes["width"] as? Int == resolution["width"] as? Int &&
                           existingRes["height"] as? Int == resolution["height"] as? Int
                }
                
                if !alreadyAdded {
                    availableResolutions.append(resolution)
                }
            }
            
            // Ordenar resoluções (da menor para a maior)
            availableResolutions.sort { (res1, res2) -> Bool in
                let width1 = res1["width"] as? Int ?? 0
                let width2 = res2["width"] as? Int ?? 0
                return width1 < width2
            }
            
            DispatchQueue.main.async {
                result(availableResolutions)
            }
        }
    }
    
    // MARK: - Image Adjustment Methods
    
    private func getCurrentImageAdjustments(result: @escaping FlutterResult) {
        DispatchQueue.main.async {
            result(self.currentAdjustments.toDict())
        }
    }

    // MARK: - Helper Methods
    
    // CIContext compartilhado para melhor desempenho
    private static let ciContext = CIContext(options: [
        .workingColorSpace: NSNull(),
        .outputColorSpace: NSNull(),
        .useSoftwareRenderer: false
    ])
    
    /// Configura a captura acelerada por hardware
    private func setupHardwareAcceleration() {
        if currentAdjustments.useHardwareAcceleration {
            // Inicializar Metal
            metalDevice = MTLCreateSystemDefaultDevice()
            if let device = metalDevice {
                commandQueue = device.makeCommandQueue()
                
                // Opções otimizadas para o contexto CIContext com Metal
                let contextOptions: [CIContextOption: Any] = [
                    .workingColorSpace: NSNull(),
                    .outputColorSpace: NSNull(),
                    .useSoftwareRenderer: false,
                    .priorityRequestLow: false,
                    .cacheIntermediates: true // Melhor performance para processamento contínuo
                ]
                
                ciContext = CIContext(mtlDevice: device, options: contextOptions)
                
                // Criar cache de textura otimizado
                var textureCache: CVMetalTextureCache?
                let cacheAttributes: [String: Any] = [
                    kCVMetalTextureCacheMaximumTextureAgeKey as String: 1 // Menor idade de textura para melhor desempenho
                ]
                CVMetalTextureCacheCreate(nil, cacheAttributes as CFDictionary, device, nil, &textureCache)
                self.textureCache = textureCache
                
                NSLog("Aceleração por hardware configurada com sucesso usando Metal")
            } else {
                NSLog("Metal não disponível neste dispositivo, usando renderização por software")
                
                // Fallback para renderização por software
                ciContext = CameraAccessPlugin.ciContext
            }
        } else {
            // Usar renderização por software
            ciContext = CameraAccessPlugin.ciContext
            NSLog("Usando renderização por software conforme solicitado")
        }
    }

    /// Atualiza os filtros com base nos ajustes atuais
    private func updateImageFilters() {
        // Log para diagnóstico
        NSLog("Atualizando filtros com: brilho=\(currentAdjustments.brightness), contraste=\(currentAdjustments.contrast), saturação=\(currentAdjustments.saturation), nitidez=\(currentAdjustments.sharpness), exposição=\(currentAdjustments.exposure), filtro=\(currentAdjustments.filter ?? "nenhum")")
        
        // Criar filtro básico de ajustes de cores
        let inputFilter = CIFilter(name: "CIColorControls")
        inputFilter?.setValue(1.0 + currentAdjustments.contrast, forKey: kCIInputContrastKey)
        inputFilter?.setValue(currentAdjustments.brightness, forKey: kCIInputBrightnessKey)
        inputFilter?.setValue(1.0 + currentAdjustments.saturation, forKey: kCIInputSaturationKey)
        
        // Definir o filtro básico como o principal inicialmente
        self.ciFilter = inputFilter
        
        // Aplicar filtro estilístico se fornecido
        if let filterName = currentAdjustments.filter, !filterName.isEmpty {
            // Criar filtro apropriado com o método existente
            if let styleFilter = createStyleFilter(name: filterName) {
                self.ciFilter = styleFilter
                NSLog("Filtro estilístico '\(filterName)' aplicado com sucesso")
            } else {
                NSLog("Filtro '\(filterName)' não encontrado, usando apenas ajustes básicos")
            }
        }
        
        // Aplicar nitidez se necessário (sempre mantendo o filtro principal atual)
        if currentAdjustments.sharpness > 0 {
            NSLog("Aplicando nitidez com intensidade \(currentAdjustments.sharpness)")
            let sharpnessFilter = CIFilter(name: "CIUnsharpMask")
            sharpnessFilter?.setValue(currentAdjustments.sharpness * 3.0, forKey: kCIInputIntensityKey)
            sharpnessFilter?.setValue(1.5, forKey: kCIInputRadiusKey)
        }
        
        NSLog("Filtros atualizados com sucesso")
    }

    /// Processa o buffer de imagem com ajustes e aceleração de GPU
    private func processImageBuffer(
        _ buffer: CVPixelBuffer,
        compressionFactor: CGFloat = 0.9,
        emergency: Bool = false
    ) throws -> Data {
        // Bloquear buffer para leitura
        CVPixelBufferLockBaseAddress(buffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(buffer, .readOnly) }
        
        // Obter dimensões para uso futuro
        let _ = CVPixelBufferGetWidth(buffer)
        let _ = CVPixelBufferGetHeight(buffer)

        // Criar CIImage a partir do buffer
        var ciImage = CIImage(cvPixelBuffer: buffer)
        
        // ZOOM: Aplicar zoom antes de outros ajustes (recortar parte central da imagem)
        if currentZoomLevel > 1.01 { // aplicar apenas se o zoom for significativo
            // Se temos zoom definido, recortar a imagem
            let originalSize = ciImage.extent.size
            
            // Calcular o novo tamanho
            let newWidth = originalSize.width / currentZoomLevel
            let newHeight = originalSize.height / currentZoomLevel
            
            // Calcular o retângulo de corte centralizado
            let centerX = originalSize.width / 2
            let centerY = originalSize.height / 2
            let cropRect = CGRect(
                x: centerX - newWidth / 2,
                y: centerY - newHeight / 2,
                width: newWidth,
                height: newHeight
            )
            
            // Recortar a imagem
            ciImage = ciImage.cropped(to: cropRect)
            
            // Escalar de volta para o tamanho original
            let scaleFilter = CIFilter(name: "CILanczosScaleTransform")!
            scaleFilter.setValue(ciImage, forKey: kCIInputImageKey)
            scaleFilter.setValue(currentZoomLevel, forKey: kCIInputScaleKey)
            
            if let outputImage = scaleFilter.outputImage {
                ciImage = outputImage
            } else {
                NSLog("❌ Falha ao aplicar zoom: o filtro de escala não produziu uma imagem de saída válida")
            }
        }
        
        // Continuar com o processamento normal...
        
        // 1. Ajustes de cores básicos (sempre aplicar para consistência)
        let colorFilter = CIFilter(name: "CIColorControls")!
        colorFilter.setValue(ciImage, forKey: kCIInputImageKey)
        colorFilter.setValue(1.0 + currentAdjustments.contrast, forKey: kCIInputContrastKey)
        colorFilter.setValue(currentAdjustments.brightness, forKey: kCIInputBrightnessKey)
        colorFilter.setValue(1.0 + currentAdjustments.saturation, forKey: kCIInputSaturationKey)
        
        if let outputImage = colorFilter.outputImage {
            ciImage = outputImage
        }
        
        // 2. Ajuste de exposição
        if abs(currentAdjustments.exposure) > 0.001 {
            let exposureFilter = CIFilter(name: "CIExposureAdjust")!
            exposureFilter.setValue(ciImage, forKey: kCIInputImageKey)
            exposureFilter.setValue(currentAdjustments.exposure * 2, forKey: kCIInputEVKey)
            
            if let outputImage = exposureFilter.outputImage {
                ciImage = outputImage
            }
        }
        
        // 3. Aplicar nitidez se necessário
        if currentAdjustments.sharpness > 0.01 {
            let sharpnessFilter = CIFilter(name: "CIUnsharpMask")!
            sharpnessFilter.setValue(ciImage, forKey: kCIInputImageKey)
            sharpnessFilter.setValue(currentAdjustments.sharpness * 3.0, forKey: kCIInputIntensityKey)
            sharpnessFilter.setValue(1.5, forKey: kCIInputRadiusKey)
            
            if let outputImage = sharpnessFilter.outputImage {
                ciImage = outputImage
            }
        }
        
        // 4. Aplicar balanço de branco via software se necessário
        if softwareWhiteBalanceEnabled {
            // Aplicar ganhos de cor RGB
            let colorMatrix = CIFilter(name: "CIColorMatrix")!
            colorMatrix.setValue(ciImage, forKey: kCIInputImageKey)
            
            // Definir valores para os canais RGB
            colorMatrix.setValue(CIVector(x: redGain, y: 0, z: 0, w: 0), forKey: "inputRVector")
            colorMatrix.setValue(CIVector(x: 0, y: greenGain, z: 0, w: 0), forKey: "inputGVector")
            colorMatrix.setValue(CIVector(x: 0, y: 0, z: blueGain, w: 0), forKey: "inputBVector")
            colorMatrix.setValue(CIVector(x: 0, y: 0, z: 0, w: 1), forKey: "inputAVector")
            
            if let outputImage = colorMatrix.outputImage {
                ciImage = outputImage
                NSLog("Aplicado balanço de branco via software: R=\(redGain), G=\(greenGain), B=\(blueGain)")
            }
        }
        
        // 5. Aplicar filtro estilístico
        if let filterName = currentAdjustments.filter, !filterName.isEmpty {
            if let styleFilter = createStyleFilter(name: filterName) {
                styleFilter.setValue(ciImage, forKey: kCIInputImageKey)
                if let outputImage = styleFilter.outputImage {
                    ciImage = outputImage
                    NSLog("Filtro estilístico '\(filterName)' aplicado com sucesso na imagem")
                }
            } else {
                NSLog("Filtro '\(filterName)' não encontrado, usando apenas ajustes básicos")
            }
        }
        
        // Usar contexto otimizado para GPU
        let context = ciContext ?? CameraAccessPlugin.ciContext
        
        // Renderizar a imagem final - ciImage já existe e não precisa ser desempacotado novamente
        // Criar um CGImage a partir do CIImage
        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else {
            throw NSError(domain: "CameraAccess", code: 3, userInfo: [NSLocalizedDescriptionKey: "Falha ao criar CGImage"])
        }
        
        // Otimização: usar NSBitmapImageRep para conversão rápida para JPEG
        let bitmapRep = NSBitmapImageRep(cgImage: cgImage)
        guard let jpegData = bitmapRep.representation(using: NSBitmapImageRep.FileType.jpeg, properties: [NSBitmapImageRep.PropertyKey.compressionFactor: compressionFactor]) else {
            throw NSError(domain: "CameraAccess", code: 4, userInfo: [NSLocalizedDescriptionKey: "Falha ao converter para JPEG"])
        }
        
        return jpegData
    }

    // Helper para criar filtros estilísticos
    private func createStyleFilter(name: String) -> CIFilter? {
        switch name.lowercased() {
        case "grayscale", "mono":
            return CIFilter(name: "CIPhotoEffectMono")
        case "sepia":
            let filter = CIFilter(name: "CISepiaTone")
            filter?.setValue(1.0, forKey: kCIInputIntensityKey)
            return filter
        case "invert":
            return CIFilter(name: "CIColorInvert")
        case "edge":
            let filter = CIFilter(name: "CIEdges")
            filter?.setValue(1.0, forKey: kCIInputIntensityKey)
            return filter
        case "noir":
            return CIFilter(name: "CIPhotoEffectNoir")
        case "vibrant":
            let filter = CIFilter(name: "CIVibrance")
            filter?.setValue(0.5, forKey: kCIInputAmountKey)
            return filter
        case "chrome":
            return CIFilter(name: "CIPhotoEffectChrome")
        case "fade":
            return CIFilter(name: "CIPhotoEffectFade")
        case "instant":
            return CIFilter(name: "CIPhotoEffectInstant")
        default:
            return nil
        }
    }

    // Rastrear tempos de processamento para melhorar desempenho
    private func trackProcessingTime(_ time: TimeInterval) {
        processingTimes.append(time)
        
        if processingTimes.count > maxProcessingTimesSamples {
            processingTimes.removeFirst()
        }
        
        if processingTimes.count >= 5 {
            let averageTime = processingTimes.reduce(0, +) / Double(processingTimes.count)
            let targetFrameTime = frameRateThrottle * 0.7 // 70% do tempo entre frames
            
            if averageTime > targetFrameTime && adaptiveQuality {
                // Processamento está demorando demais, reduzir qualidade
                adaptQualityDown()
            } else if averageTime < targetFrameTime * 0.5 {
                // Processamento rápido, pode tentar aumentar qualidade
                tryAdaptQualityUp()
            }
        }
    }

    // Reduzir qualidade para melhorar desempenho
    private func adaptQualityDown() {
        // Aumentar intervalo entre frames (reduzir FPS)
        frameRateThrottle = min(1.0 / 15.0, frameRateThrottle * 1.2)
        
        NSLog("Adaptando para menor qualidade: \(1.0/frameRateThrottle) FPS")
        
        // Resetar métricas
        processingTimes.removeAll()
    }

    // Aumentar qualidade quando desempenho permitir
    private func tryAdaptQualityUp() {
        guard adaptiveQuality else { return }
        
        // Se estiver performando bem, aumentar qualidade
        if frameRateThrottle > 1.0 / 60.0 {
            frameRateThrottle = max(1.0 / 60.0, frameRateThrottle * 0.9)
            NSLog("Adaptando para maior qualidade: \(1.0/frameRateThrottle) FPS")
        }
        
        // Resetar métricas para próxima avaliação
        processingTimes.removeAll()
    }

    // Adicionar método que estava faltando para processamento com Metal
    private func processFrameWithMetal(_ buffer: CVPixelBuffer) throws -> Data {
        // Verificar se temos recursos Metal
        guard let _ = self.metalDevice,
              let commandQueue = self.commandQueue,
              let textureCache = self.textureCache,
              let ciContext = self.ciContext else {
            NSLog("❌ Recursos Metal não disponíveis, usando CoreImage")
            return try processFrameWithCoreImage(buffer)
        }
        
        // Criar uma textura Metal a partir do buffer de pixels
        let width = CVPixelBufferGetWidth(buffer)
        let height = CVPixelBufferGetHeight(buffer)
        
        var texture: CVMetalTexture?
        let status = CVMetalTextureCacheCreateTextureFromImage(
            nil,
            textureCache,
            buffer,
            nil,
            .bgra8Unorm,
            width,
            height,
            0,
            &texture
        )
        
        guard status == kCVReturnSuccess, let metalTexture = texture else {
            NSLog("❌ Falha ao criar textura Metal: \(status)")
            // Fallback para CoreImage
            return try processFrameWithCoreImage(buffer)
        }
        
        // Obter a textura Metal real
        guard let mtlTexture = CVMetalTextureGetTexture(metalTexture) else {
            NSLog("❌ Falha ao obter textura MTL")
            return try processFrameWithCoreImage(buffer)
        }
        
        // Criar CIImage a partir da textura
        var ciImage = CIImage(mtlTexture: mtlTexture, options: nil)
        
        // Se criação falhou, tentar abordagem alternativa
        if ciImage == nil {
            ciImage = CIImage(cvPixelBuffer: buffer)
            
            if ciImage == nil {
                NSLog("❌ Falha ao criar CIImage a partir de textura ou buffer")
                throw NSError(domain: "CameraAccess", code: 3, userInfo: [NSLocalizedDescriptionKey: "Falha ao criar CIImage"])
            }
        }
        
        // Aplicar ajustes usando Core Image
        if let image = ciImage {
            // Aplicar cada filtro de ajuste
            
            // 1. Ajustes básicos (brilho, contraste, saturação)
            let colorFilter = CIFilter(name: "CIColorControls")!
            colorFilter.setValue(image, forKey: kCIInputImageKey)
            colorFilter.setValue(1.0 + currentAdjustments.contrast, forKey: kCIInputContrastKey)
            colorFilter.setValue(currentAdjustments.brightness, forKey: kCIInputBrightnessKey)
            colorFilter.setValue(1.0 + currentAdjustments.saturation, forKey: kCIInputSaturationKey)
            
            if let outputImage = colorFilter.outputImage {
                ciImage = outputImage
            }
            
            // 2. Exposição
            if abs(currentAdjustments.exposure) > 0.001 {
                let exposureFilter = CIFilter(name: "CIExposureAdjust")!
                exposureFilter.setValue(ciImage, forKey: kCIInputImageKey)
                exposureFilter.setValue(currentAdjustments.exposure * 2, forKey: kCIInputEVKey)
                
                if let outputImage = exposureFilter.outputImage {
                    ciImage = outputImage
                }
            }
            
            // 3. Nitidez
            if currentAdjustments.sharpness > 0.01 {
                let sharpnessFilter = CIFilter(name: "CIUnsharpMask")!
                sharpnessFilter.setValue(ciImage, forKey: kCIInputImageKey)
                sharpnessFilter.setValue(currentAdjustments.sharpness * 3.0, forKey: kCIInputIntensityKey)
                sharpnessFilter.setValue(1.5, forKey: kCIInputRadiusKey)
                
                if let outputImage = sharpnessFilter.outputImage {
                    ciImage = outputImage
                }
            }
            
            // 4. Filtros estilísticos
            if let filterName = currentAdjustments.filter, !filterName.isEmpty {
                if let styleFilter = createStyleFilter(name: filterName) {
                    styleFilter.setValue(ciImage, forKey: kCIInputImageKey)
                    if let outputImage = styleFilter.outputImage {
                        ciImage = outputImage
                        NSLog("Filtro estilístico '\(filterName)' aplicado com sucesso ao frame")
                    }
                } else {
                    NSLog("Filtro '\(filterName)' não encontrado, usando apenas ajustes básicos")
                }
            }
            
            // Criar um commandBuffer para renderização
            guard commandQueue.makeCommandBuffer() != nil else {
                NSLog("❌ Falha ao criar command buffer")
                return try processFrameWithCoreImage(buffer)
            }
            
            // Renderizar a imagem final - ciImage já existe e não precisa ser desempacotado novamente
            // Criar um CGImage a partir do CIImage
            if let unwrappedImage = ciImage {
                guard let cgImage = ciContext.createCGImage(unwrappedImage, from: unwrappedImage.extent) else {
                    NSLog("❌ Falha ao criar CGImage")
                    throw NSError(domain: "CameraAccess", code: 5, userInfo: [NSLocalizedDescriptionKey: "Falha ao criar CGImage"])
                }
                
                // Converter para JPEG com NSBitmapImageRep (mais eficiente no macOS)
                let bitmapRep = NSBitmapImageRep(cgImage: cgImage)
                let compressionFactor: CGFloat = 0.9 // Ajuste conforme necessário
                
                guard let jpegData = bitmapRep.representation(using: NSBitmapImageRep.FileType.jpeg, properties: [NSBitmapImageRep.PropertyKey.compressionFactor: compressionFactor]) else {
                    NSLog("❌ Falha ao converter para JPEG")
                    throw NSError(domain: "CameraAccess", code: 6, userInfo: [NSLocalizedDescriptionKey: "Falha ao converter para JPEG"])
                }
                
                return jpegData
            } else {
                NSLog("❌ CIImage é nil após processamento")
                throw NSError(domain: "CameraAccess", code: 7, userInfo: [NSLocalizedDescriptionKey: "CIImage é nil"])
            }
        } else {
            NSLog("❌ CIImage é nil após processamento")
            throw NSError(domain: "CameraAccess", code: 7, userInfo: [NSLocalizedDescriptionKey: "CIImage é nil"])
        }
    }
    
    // Adicionar método para processamento com CoreImage
    private func processFrameWithCoreImage(_ buffer: CVPixelBuffer) throws -> Data {
        return try processImageBuffer(buffer)
    }
    
    // Adicionar método captureCurrentFrame que estava faltando
    private func captureCurrentFrame(forceCapture: Bool, completion: @escaping (Data?, String?) -> Void) {
        captureFrame(forceCapture: forceCapture) { result in
            if let error = result as? FlutterError {
                completion(nil, error.message)
            } else if let data = (result as? FlutterStandardTypedData)?.data {
                completion(data, nil)
            } else {
                completion(nil, "Erro desconhecido ao capturar frame")
            }
        }
    }

    // MARK: - Zoom Methods
    
    private func getZoomLevel(result: @escaping FlutterResult) {
        // No macOS, as APIs de zoom de câmera como videoZoomFactor não estão disponíveis
        // Usaremos nossa própria implementação baseada em variáveis internas
        if !_isCameraInitialized {
            result(FlutterError(code: "CAMERA_UNAVAILABLE", 
                              message: "Câmera não disponível", 
                              details: nil))
            return
        }
        
        // Retornar o valor armazenado internamente
        result(currentZoomLevel)
    }
    
    private func getMaxZoomLevel(result: @escaping FlutterResult) {
        // No macOS, as APIs de zoom como videoMaxZoomFactor não estão disponíveis
        // Retornar um valor constante ou configurado
        result(maxZoomLevel)
    }
    
    private func setZoomLevel(level: CGFloat, result: @escaping FlutterResult) {
        if !_isCameraInitialized {
            result(FlutterError(code: "CAMERA_UNAVAILABLE", 
                              message: "Câmera não disponível", 
                              details: nil))
            return
        }
        
        // Garantir que o nível de zoom esteja dentro dos limites definidos
        let clampedZoom = max(minZoomLevel, min(level, maxZoomLevel))
        
        // Em macOS, implementamos zoom via software (recorte da imagem)
        let oldZoom = currentZoomLevel
        currentZoomLevel = clampedZoom
        
        NSLog("📸 Zoom alterado de \(oldZoom)x para \(clampedZoom)x - Este zoom será aplicado no próximo frame capturado")
        
        result(true)
    }

    // MARK: - White Balance Methods
    
    private func setWhiteBalance(mode: String, result: @escaping FlutterResult) {
        sessionQueue.async { [weak self] in
            guard let self = self,
                  self._isCameraInitialized else {
                DispatchQueue.main.async {
                    result(FlutterError(code: "CAMERA_UNAVAILABLE", 
                                      message: "Câmera não disponível", 
                                      details: nil))
                }
                return
            }
            
            // Armazenar o modo atual
            self.currentWhiteBalanceMode = mode
            
            if let device = self.currentDevice, device.isWhiteBalanceModeSupported(.locked) {
                do {
                    try device.lockForConfiguration()
                    
                    // Aplicar o modo apropriado
                    switch mode.lowercased() {
                    case "auto":
                        if device.isWhiteBalanceModeSupported(.continuousAutoWhiteBalance) {
                            device.whiteBalanceMode = .continuousAutoWhiteBalance
                            NSLog("Balanço de branco configurado para: auto")
                            self.softwareWhiteBalanceEnabled = false
                        }
                    case "daylight", "sunny", "cloudy", "fluorescent", "incandescent", "tungsten":
                        // No macOS, não temos controle granular sobre temperatura de cor
                        // como no iOS. Definimos para modo locked, que mantém o ajuste atual
                        if device.isWhiteBalanceModeSupported(.locked) {
                            device.whiteBalanceMode = .locked
                            NSLog("Balanço de branco configurado para modo bloqueado: \(mode)")
                        }
                    default:
                        // Modo auto como fallback
                        if device.isWhiteBalanceModeSupported(.continuousAutoWhiteBalance) {
                            device.whiteBalanceMode = .continuousAutoWhiteBalance
                            NSLog("Modo de balanço de branco desconhecido, usando auto")
                            self.softwareWhiteBalanceEnabled = false
                        }
                    }
                    
                    device.unlockForConfiguration()
                    
                    DispatchQueue.main.async {
                        result(true)
                    }
                } catch {
                    NSLog("Erro ao configurar balanço de branco no hardware: \(error). Usando simulação por software.")
                    // Falhou no hardware, vamos usar implementação por software
                    self.setupSoftwareWhiteBalance(mode: mode)
                    DispatchQueue.main.async {
                        result(true)
                    }
                }
            } else {
                NSLog("Dispositivo não suporta configuração de balanço de branco. Usando simulação por software.")
                // Usar implementação por software
                self.setupSoftwareWhiteBalance(mode: mode)
                DispatchQueue.main.async {
                    result(true)
                }
            }
        }
    }
    
    // Configurar simulação de balanço de branco por software
    private func setupSoftwareWhiteBalance(mode: String) {
        softwareWhiteBalanceEnabled = true
        
        // Configurar ganhos RGB com base no modo solicitado
        switch mode.lowercased() {
        case "auto":
            // Em auto, usamos valores neutros
            redGain = 1.0
            greenGain = 1.0
            blueGain = 1.0
            softwareWhiteBalanceEnabled = false
            NSLog("Balanço de branco por software desativado (modo auto)")
            
        case "daylight", "sunny":
            // Temperatura 5500K - cor neutra levemente amarelada
            redGain = 1.0
            greenGain = 0.95
            blueGain = 0.9
            NSLog("Balanço de branco por software: daylight/sunny (5500K)")
            
        case "cloudy":
            // Temperatura 6500K - cor neutra levemente azulada
            redGain = 0.95
            greenGain = 0.95
            blueGain = 1.05
            NSLog("Balanço de branco por software: cloudy (6500K)")
            
        case "fluorescent":
            // Temperatura 4000K - cor levemente esverdeada
            redGain = 0.9
            greenGain = 1.0
            blueGain = 1.0
            NSLog("Balanço de branco por software: fluorescent (4000K)")
            
        case "incandescent", "tungsten":
            // Temperatura 2700K - cor amarelada/alaranjada
            redGain = 1.2
            greenGain = 0.95
            blueGain = 0.8
            NSLog("Balanço de branco por software: incandescent/tungsten (2700K)")
            
        default:
            // Valor padrão neutro
            redGain = 1.0
            greenGain = 1.0
            blueGain = 1.0
            softwareWhiteBalanceEnabled = false
            NSLog("Modo de balanço de branco desconhecido, desativando simulação por software")
        }
    }
}

// MARK: - AVCaptureVideoDataOutputSampleBufferDelegate
extension CameraAccessPlugin: AVCaptureVideoDataOutputSampleBufferDelegate {
    public func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        // Verificar se temos um pixel buffer válido
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else {
            NSLog("⚠️ Erro: Pixel buffer inválido recebido do AVCaptureOutput")
            return
        }
        
        // Incrementar contador total
        totalFramesProcessed += 1
        
        // Verificar controle de taxa com timeout para evitar bloqueios
        let now = Date()
        let timeSinceLastFrame = now.timeIntervalSince(lastCaptureTime)
        
        if timeSinceLastFrame < frameRateThrottle {
            // Ignorar este frame para manter a taxa desejada
            droppedFrames += 1
            return
        }
        
        // Usar wait com timeout para evitar bloqueios permanentes
        if frameSemaphore.wait(timeout: .now() + .milliseconds(5)) == .success {
            defer { frameSemaphore.signal() }
            
            // Armazenar a referência ao buffer - Swift gerencia a memória automaticamente
            lastFrame = pixelBuffer
            lastCaptureTime = now
            
            // Log para diagnóstico
            _ = CVPixelBufferGetWidth(pixelBuffer)
            _ = CVPixelBufferGetHeight(pixelBuffer)
        } else {
            // Se o semáforo está bloqueado, incrementar contagem de frames descartados
            droppedFrames += 1
            
            // Adaptação automática de qualidade para melhorar desempenho
            if adaptiveQuality {
                consecutiveSlowFrames += 1
                if consecutiveSlowFrames >= maxConsecutiveSlowFrames {
                    consecutiveSlowFrames = 0
                    // Reduzir qualidade/frame rate para melhorar desempenho
                    adaptQualityDown()
                }
            }
        }
    }
    
    // Método para criar uma imagem JPEG vazia para casos de erro
    private func createEmptyJpegImage(width: Int, height: Int) -> Data? {
        // Criar uma imagem em branco
        NSLog("🔄 Criando imagem vazia de fallback: \(width)x\(height)")
        
        let emptyImage = NSImage(size: NSSize(width: width, height: height))
        
        // Preencher com cor preta
        emptyImage.lockFocus()
        NSColor.black.drawSwatch(in: NSRect(x: 0, y: 0, width: width, height: height))
        emptyImage.unlockFocus()
        
        // Converter para JPEG
        if let tiffData = emptyImage.tiffRepresentation,
           let bitmapRep = NSBitmapImageRep(data: tiffData),
           let jpegData = bitmapRep.representation(using: NSBitmapImageRep.FileType.jpeg, properties: [:]) {
            NSLog("✅ Imagem vazia criada com sucesso: \(jpegData.count) bytes")
            return jpegData
        }
        
        NSLog("❌ Falha ao criar imagem vazia")
        return nil
    }
}