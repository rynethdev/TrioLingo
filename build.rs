fn main() {
    println!("cargo:rerun-if-changed=web");
    println!("cargo:rerun-if-changed=content");
}
