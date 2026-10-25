struct Widget { w: u32 }

trait Runner { fn run(&self); }

impl Runner for Widget {
    fn run(&self) {
        if self.w > 0 {
            helper(self.w);
        }
    }
}

fn helper(n: u32) {
    match n { 0 => cleanup(), _ => {} }
}

fn cleanup() {
    let conn = Connection::new();
    drop(conn);
    panic!("bad state");
}
