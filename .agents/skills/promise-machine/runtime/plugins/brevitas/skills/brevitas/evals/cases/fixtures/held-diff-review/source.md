diff --git a/plugins/pandects/specimens/Sound.sol b/plugins/pandects/specimens/Sound.sol
index 0346254..e902eb4 100644
--- a/plugins/pandects/specimens/Sound.sol
+++ b/plugins/pandects/specimens/Sound.sol
@@ -222,16 +222,25 @@ contract Sound is ICreditObservables, IWithdrawalQueueObservables {
-    /// The fee is capped at the claims that are not already reserved. Value
-    /// earmarked against a recorded withdrawal has been promised to a lender
-    /// who asked for it, and a protocol that takes its fee out of that is
-    /// taking money it already owed to somebody leaving. Without the cap, a fee
-    /// charged after a reservation drops claims below what is reserved, which
-    /// is what `reserves-backed-by-claims` refuses.
+    /// The fee is capped at the claims the open batches are not already owed.
+    /// Value recorded against a withdrawal has been promised to a lender who
+    /// asked for it, and a protocol that takes its fee out of that is taking
+    /// money it already owed to somebody leaving.
+    ///
+    /// The cap measures against the queue rather than against the earmark, and
+    /// the difference is the whole of `claims/pooled-claims-cover-open-batches/v1`.
+    /// An earmark cannot exceed what is held, so in an illiquid system it sits
+    /// below what the batches are owed, and a cap taken against it lets the fee
+    /// reach the shortfall.
     function accrueFee(uint256 amount) external virtual {
-        uint256 available = claims > reserved ? claims - reserved : 0;
+        uint256 queued = unpaidTotal();
+        uint256 available = claims > queued ? claims - queued : 0;
         uint256 value = bounded(amount);
         if (value > available) {
             value = available;
@@ -248,8 +257,17 @@ contract Sound is ICreditObservables, IWithdrawalQueueObservables {
     /// @notice Record a withdrawal claim and earmark held assets against it.
+    /// @dev Bounded by the pooled claim the open batches are not already owed,
+    /// and deliberately not by what the system holds. A lender may ask to leave
+    /// a system that cannot pay them, which is the state the corpus exists for.
+    /// Bounding by the pooled claim alone, as this once did, let one pool be
+    /// queued twice: two requests each within the pool, together beyond it,
+    /// recording more owed than the system owes in total.
     function reserve(uint256 amount) external virtual {
-        uint256 ceiling = claims < held ? claims : held;
+        uint256 ceiling = claims > unpaidTotal() ? claims - unpaidTotal() : 0;
         uint256 value = bounded(amount);
         if (value > ceiling) {
             value = ceiling;
