import java.util.Optional;
class A { String f(boolean b) { Optional<String> o = find(); if (b) { log(); } return o.get(); } }
