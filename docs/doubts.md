# Doubts — decisions to revisit

## Bulk Approve High-Confidence Answers

**What it was:** A button on the QuestionnaireDetail sidebar that bulk-approved all high-confidence answers at once.

**Why it was removed:** No one is likely to go back and review answers after they've been bulk-approved. In a GRC context where answer accuracy matters, this creates a risk of wrong/slightly-off answers slipping into the final export unchecked — especially if someone uses it just to finish quickly.

**Why it might be worth adding back:** High-confidence answers are already filtered by the AI's confidence score, so the quality floor is higher. Could save time on large questionnaires with many obvious answers.

**Things to figure out if re-adding:**
- Should it move answers to a "pending review" state instead of directly approved?
- Should it be restricted to owner/admin only?
- Should there be a way to see which answers were bulk-approved vs individually reviewed?
