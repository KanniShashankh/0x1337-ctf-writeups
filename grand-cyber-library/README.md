# The Grand Cyber Library

- **Category:** Web
- **Flag:** `0x1337{l1br4ry_c4rd_pr3v13w_ID0R_t0_priv4t3_dr4ft}`
- **Files:** [`files/wordfence.zip`](files/wordfence.zip) (white-box source of the `deccan-library` plugin), [`files/solve.py`](files/solve.py)
- **Service:** `http://40.81.242.56:30755` (also `30352`)
- **Author:** delayLlama

## Challenge

> The Grand Cyber Library runs on WordPress. Fully patched, they say. Wpscan finds nothing. They also wrote their own plugin and left registration open for "free library cards".

WordPress core is patched, so the bug is in the custom `deccan-library` plugin.
The README in the zip says it plainly: *"wpscan will find nothing — audit this.
See /wp-json/ and the Library page after registering."*

## Key observations

The plugin exposes member draft previews through two transports — a public REST
route `deccan/v1/preview` (gated by a WP nonce) and `admin-ajax.php?action=deccan_preview`
(cookie-authed, nonce-checked). Both funnel into one helper:

```php
function deccan_fetch_post($id) {
    if (!$id) return new WP_Error('bad', 'missing id');
    $p = get_post($id);
    if (!$p || $p->post_type !== 'post') return new WP_Error('notfound', 'no such draft');
    if (!current_user_can('read')) return new WP_Error('forbidden', 'members only');
    // NOTE: widget always sends the user's own id, so ownership check omitted for speed.
    return ['id'=>$p->ID, 'title'=>$p->post_title, 'status'=>$p->post_status, 'body'=>$p->post_content];
}
```

**The IDOR is handed to you in a comment.** The only authz check is
`current_user_can('read')` — the `read` capability every Subscriber has. There is
**no ownership check and no post-status check**, so any logged-in member can read
any post of type `post` by numeric ID, including other users' private drafts and
the admin's unpublished posts. The flag lives in one of those.

Supporting details that make the chain trivial:

- Registration is open and the plugin sets the password directly from the
  `deccan_pass` field on the register form (`user_register` → `wp_update_user`),
  so there is **no email confirmation** — instant working account.
- The `/library/` page runs `wp_localize_script` and embeds a valid
  `deccan_preview` nonce (`DECCAN.nonce`) in the HTML for any logged-in user.
- The `deccan/v1/search` route and the "public REST" comments are deliberate
  decoys — the search is properly `prepare()`d, and the public REST route's nonce
  check fails for cookie-less callers (the code comments even admit the "public
  route" claim is a lie). The real path is admin-ajax.

## Solution

1. Register a free card: `POST /wp-login.php?action=register` with `user_login`,
   `user_email`, `deccan_pass` (≥8 chars).
2. Log in: `POST /wp-login.php` with `log`/`pwd` (+ `wordpress_test_cookie`).
3. Fetch `/library/` and scrape `DECCAN.nonce` from the inline localized script.
4. Sweep IDs against `admin-ajax.php?action=deccan_preview&nonce=<n>&id=<i>` with
   the auth cookies, reading each draft's `body` until the flag appears.

See [`files/solve.py`](files/solve.py) for the full automated chain.

### Gotcha

WordPress `siteurl`/`home` are set to `localhost:1337`, so any request to the
real `IP:port` triggers a canonical 301 back to `localhost:1337` (unreachable
from outside), and `login_redirect` sends members to `home_url('/library/')` on
that same dead host. Fix: send a `Host: localhost:1337` header on every request
and disable automatic redirect following — the cookies still bind to the
connection host, so auth carries through.

### Result

The sweep lands on **post ID 5**, status `private`:

```json
{"id":5,"title":"Acquisitions memo (internal)","status":"private",
 "body":"Reminder: do NOT share the vault code outside staff. Vault: 0x1337{l1br4ry_c4rd_pr3v13w_ID0R_t0_priv4t3_dr4ft} -- head librarian."}
```

**Flag:** `0x1337{l1br4ry_c4rd_pr3v13w_ID0R_t0_priv4t3_dr4ft}`

## Lessons

- `current_user_can('read')` is authentication, not authorization. Object-level
  access needs an explicit owner/`current_user_can('read_post', $id)` check.
- "The client always sends the right ID" is never an access-control boundary.
- Verbose source comments that explain *why* a check was skipped are a gift to an
  auditor — the vuln was literally annotated.
