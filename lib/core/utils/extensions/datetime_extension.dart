extension DateTimeExtension on DateTime {
  int get daysAgo {
    final now = DateTime.now();
    return now.difference(this).inDays;
  }

  String get timeAgo {
    final now = DateTime.now();
    final difference = now.difference(this);

    if (difference.inDays > 365) {
      return '${(difference.inDays / 365).floor()}a atrás';
    } else if (difference.inDays > 30) {
      return '${(difference.inDays / 30).floor()}m atrás';
    } else if (difference.inDays > 0) {
      return '${difference.inDays}d atrás';
    } else if (difference.inHours > 0) {
      return '${difference.inHours}h atrás';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes}m atrás';
    } else {
      return 'Agora';
    }
  }
}