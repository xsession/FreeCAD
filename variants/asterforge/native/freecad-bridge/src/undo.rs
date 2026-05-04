use crate::BridgeDocumentSnapshot;

/// Manages an undo/redo stack around a `BridgeDocumentSnapshot`.
#[derive(Debug, Clone)]
pub struct UndoStack {
    undo: Vec<BridgeDocumentSnapshot>,
    redo: Vec<BridgeDocumentSnapshot>,
    max_depth: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum UndoAction {
    Undo,
    Redo,
}

#[derive(Debug, Clone)]
pub struct UndoActionResult {
    pub accepted: bool,
    pub status_message: String,
    pub snapshot: Option<BridgeDocumentSnapshot>,
}

impl UndoStack {
    pub fn new(max_depth: usize) -> Self {
        Self {
            undo: Vec::new(),
            redo: Vec::new(),
            max_depth,
        }
    }

    pub fn push(&mut self, snapshot: &BridgeDocumentSnapshot) {
        if self.undo.len() >= self.max_depth {
            self.undo.remove(0);
        }
        self.undo.push(snapshot.clone());
        self.redo.clear();
    }

    pub fn undo(&mut self, current: &BridgeDocumentSnapshot) -> Option<BridgeDocumentSnapshot> {
        let previous = self.undo.pop()?;
        self.redo.push(current.clone());
        Some(previous)
    }

    pub fn redo(&mut self, current: &BridgeDocumentSnapshot) -> Option<BridgeDocumentSnapshot> {
        let next = self.redo.pop()?;
        self.undo.push(current.clone());
        Some(next)
    }

    pub fn can_undo(&self) -> bool {
        !self.undo.is_empty()
    }

    pub fn can_redo(&self) -> bool {
        !self.redo.is_empty()
    }

    pub fn undo_depth(&self) -> usize {
        self.undo.len()
    }

    pub fn redo_depth(&self) -> usize {
        self.redo.len()
    }
}

pub fn apply_undo_action(
    stack: &mut UndoStack,
    current: &BridgeDocumentSnapshot,
    action: UndoAction,
) -> UndoActionResult {
    let restored = match action {
        UndoAction::Undo => stack.undo(current),
        UndoAction::Redo => stack.redo(current),
    };

    match restored {
        Some(snapshot) => UndoActionResult {
            accepted: true,
            status_message: match action {
                UndoAction::Undo => "Undo applied".into(),
                UndoAction::Redo => "Redo applied".into(),
            },
            snapshot: Some(snapshot),
        },
        None => UndoActionResult {
            accepted: false,
            status_message: match action {
                UndoAction::Undo => "Nothing to undo".into(),
                UndoAction::Redo => "Nothing to redo".into(),
            },
            snapshot: None,
        },
    }
}