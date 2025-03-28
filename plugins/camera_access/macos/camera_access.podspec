#
# To learn more about a Podspec see http://guides.cocoapods.org/syntax/podspec.html.
# Run `pod lib lint camera_access.podspec` to validate before publishing.
#
Pod::Spec.new do |s|
  s.name             = 'camera_access'
  s.version          = '0.0.1'
  s.summary          = 'A plugin for accessing camera with hardware acceleration and image adjustments'
  s.description      = <<-DESC
A Flutter plugin that provides access to device cameras with support for hardware acceleration, configurable resolution, and image adjustments for macOS and Windows.
                       DESC
  s.homepage         = 'http://example.com'
  s.license          = { :file => '../LICENSE' }
  s.author           = { 'Your Company' => 'email@example.com' }
  s.source           = { :path => '.' }
  s.source_files     = 'classes/**/*'
  s.dependency 'FlutterMacOS'

  s.platform = :osx, '10.11'
  s.pod_target_xcconfig = { 'DEFINES_MODULE' => 'YES' }
  s.swift_version = '5.0'
end 