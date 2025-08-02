import 'package:truncate/truncate.dart';

String normalizeStageName(String name, {int maxLength = 60}) {
  return truncate(name.replaceAll('_', ' '), maxLength);
}
