---
title: Breadcrumb Removal Test
Status: published
---

Breadcrumbs with existing links (should show link without prefix):
X::[[internal_link]]
Up::[[tags]]

Breadcrumbs with non-existing links (should be completely removed):
X::[[nonexistent_article]]
Down::[[another_missing]]

Mixed content:
Some text X::[[internal_link]] more text.
Another line Up::[[missing_link]] with text.