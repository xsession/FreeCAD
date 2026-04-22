pub mod asterforge {
    pub mod protocol {
        pub mod v1 {
            include!(concat!(env!("OUT_DIR"), "/asterforge.protocol.v1.rs"));
        }
    }
}

#[cfg(test)]
mod tests {
    use super::asterforge::protocol::v1::{BootPayload, CommandInvocation};

    #[test]
    fn generated_messages_are_available() {
        let payload = BootPayload::default();
        let invocation = CommandInvocation::default();

        assert!(payload.object_tree.is_empty());
        assert_eq!(invocation.arguments.len(), 0);
    }
}