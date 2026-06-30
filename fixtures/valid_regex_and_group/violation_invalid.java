import java.util.regex.Pattern;

class InvalidRegex {
  Pattern build() {
    return Pattern.compile("(unclosed");
  }
}
