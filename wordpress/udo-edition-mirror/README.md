# uDO Edition Mirror

uCore-Publish owns this WordPress extension. It uses WordPress posts and revisions for reviewed editions. Its storage cost is the reviewed edition HTML plus WordPress revision history. Deactivating the extension removes its routes. WordPress retains edition records for review or export.

Use one WordPress installation with hosting aliases for `udo.guide` and `udo.place`, both with HTTPS. Configure the hosting layer to preserve the requested hostname and send edition paths to WordPress. Check that the hosting layer allows the mirror host through without redirecting it to the primary host. Keep `cdn.udo.guide` on its graphics origin.

Create a draft `udo_edition` post with the approved edition HTML and a post slug of `{edition-slug}-{revision}`. Review links, headings and assets in the generated HTML before publishing the record. For example, the slug `field-guide-3` serves `/editions/field-guide/3/` on both hosts. Both copies declare the guide URL canonical. Relative links between edition pages work on either host. Publishing or withdrawing the record affects both routes. Configure any hosting caches to bypass or purge these routes on changes.

This package serves reviewed edition pages. Vault link resolution happens before import. The spatial index, form integration and fallback tasks have separate contracts and remain outside this package.

## WPMU DEV site 4415738

The current primary domain is `cdn.udo.guide`. WPMU DEV documents that extra domains on a hosted site resolve to the primary domain. Confirm host-preserving routing before adding edition hosts. If the hosting plan redirects secondary domains, route the two edition hostnames through a separate HTTPS proxy or publish the same edition output to two static origins. Preserve the CDN hostname and its existing asset routes during rollout.

[WPMU DEV primary domain behavior](https://wpmudev.com/docs/hosting/overview-dashboard/#domains)
