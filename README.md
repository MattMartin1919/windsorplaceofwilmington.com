# Windsor Place of Wilmington — static site

Replacement for windsorplaceofwilmington.com. Plain HTML/CSS, no framework, about 100 KB of CSS, JS and fonts in total.

## First run

```sh
./get-images.sh      # pulls photos, logo, floor-plan PDFs and the EOAI certificate from the old site
python3 build.py --serve   # writes the finished site to public/ and previews it
```

The preview address is printed when it starts (currently http://localhost:8000/windsorplaceofwilmington.com/).

Run `get-images.sh` **before** the old host is shut off — afterward those files are gone.

## Editing

- Page text: `content/*.html`. The comment at the top of each file holds its URL, title tag and meta description.
- Site address, phone, address, service-area towns, nav, redirects: the `SITE`, `NAV` and `REDIRECTS` blocks at the top of `build.py`.
- Testimonials: `QUOTES_ALL` in `build.py`.
- Styles: `static/css/site.css` (colors are the variables at the top).
- Extra gallery photos: drop them in `static/img/gallery/`. The filename becomes the caption (`the-library.jpg` → "The library").

Reusable blocks you can drop into any page: `{{cta_buttons}}`, `{{care_table}}`, `{{quotes}}`, `{{quotes_all}}`, `{{cta_band}}`, `{{tour_form}}`, `{{gallery}}`, and `{{img name "alt text"}}`.

## Deploying

The site is hosted on GitHub Pages at https://mattmartin1919.github.io/windsorplaceofwilmington.com/. Every push to `main` runs `.github/workflows/pages.yml`, which runs `build.py` and publishes `public/`. You don't commit `public/`; it's in `.gitignore`.

Preview-mode settings in `SITE` (`build.py`):

- `domain` is the site's full address. Links are prefixed with any path after the domain (`/windsorplaceofwilmington.com`). To move to a custom domain, change it to `https://www.windsorplaceofwilmington.com`, set the domain under the repo's Settings → Pages, and point DNS at GitHub.
- `noindex: True` keeps search engines out. Set it to `False` at launch.
- `phone`, `tel`, `fax` and `fax_tel` are placeholder 555 numbers. The real ones are in the comment beside them.
- The tour and careers forms have `data-placeholder`. They check required fields, then go to the thank-you page **without sending anything**. To connect them, set each form's `action` to a form service such as Formspree and remove `data-placeholder`.

GitHub Pages can't do server redirects, so `_redirects` (old-URL 301s for Netlify or Cloudflare Pages) has no effect there.

## SEO already in place

- One page per service, each targeting its own search ("assisted living Wilmington MA", "memory care Wilmington MA", "respite care"…)
- Unique title and meta description on every page, canonical URLs, Open Graph tags
- LocalBusiness structured data (address, phone, services, amenities, areas served), breadcrumbs, and FAQPage data built automatically from the FAQ sections
- `sitemap.xml`, `robots.txt`
- 301 redirects from every old URL (`/service/alzheimers-care` → `/memory-care/`, etc.), so existing Google rankings and inbound links carry over
- Google Tag Manager and the Search Console verification tag are switched off for now. To turn them back on, fill in `gtm` and `google_verify` in `build.py` (the old IDs are in the comment there) and rebuild. The Facebook domain verification tag is still in place.
- Self-hosted fonts, responsive images, no layout shift, mobile tap-to-call bar

After launch (once Search Console verification is back on, or verified via DNS): submit `https://www.windsorplaceofwilmington.com/sitemap.xml` in Search Console, and make sure the Google Business Profile uses the same name, address and phone as the site.

## Check before launch

- [ ] **Apartment count.** The old site says 87 on one page and 88 on another, so the new site leaves the number out. Add it once confirmed.
- [ ] **"We'll call you back within one business day"** on the tour form and thank-you page. Keep this only if the team can meet it.
- [ ] **Memory care FAQ, "Can a spouse live nearby?"** This is inferred from the layout of the building, not stated on the old site.
- [ ] **Sample day on the home page.** The times are illustrative. Swap in a real day from the activity calendar if you like.
- [ ] The old site also listed a toll-free relocation line, 1-866-988-2330. It isn't used here. Add it if it's still active.
- [ ] Testimonials are excerpts from the old Testimonials page. Confirm you're still happy to publish them.
