fn main() {
    let proto = "../../../protocol/proto/asterforge.proto";
    println!("cargo:rerun-if-changed={proto}");

    let protoc = protoc_bin_vendored::protoc_bin_path().expect("vendored protoc");
    // SAFETY: build scripts run in a single process context for cargo here.
    unsafe {
        std::env::set_var("PROTOC", protoc);
    }

    prost_build::Config::new()
        .compile_protos(&[proto], &["../../../protocol/proto"])
        .expect("compile asterforge protocol");
}