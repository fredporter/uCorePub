<?php
/**
 * Plugin Name: uDO Edition Mirror
 * Description: Serves reviewed editions on udo.guide and udo.place from one WordPress site.
 * Version: 0.1.1
 */

defined('ABSPATH') || exit;

add_action('init', static function () {
    register_post_type('udo_edition', [
        'label' => 'uDO Editions',
        'public' => false,
        'show_ui' => true,
        'show_in_rest' => false,
        'supports' => ['title', 'editor', 'revisions'],
        'rewrite' => false,
        'query_var' => false,
    ]);
});

add_action('template_redirect', static function () {
    $host = strtolower($_SERVER['HTTP_HOST'] ?? '');
    if (!in_array($host, ['udo.guide', 'udo.place'], true)) {
        return;
    }

    $path = explode('?', $_SERVER['REQUEST_URI'] ?? '', 2)[0];
    if (!preg_match('~^/editions/([a-z0-9][a-z0-9-]{0,119})/([1-9][0-9]{0,8})/?$~D', $path, $match)) {
        return;
    }

    $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
    if ($method !== 'GET' && $method !== 'HEAD') {
        header('Allow: GET, HEAD');
        status_header(405);
        exit;
    }

    $slug = $match[1] . '-' . $match[2];
    $editions = get_posts([
        'post_type' => 'udo_edition',
        'post_status' => 'publish',
        'name' => $slug,
        'has_password' => false,
        'posts_per_page' => 1,
    ]);
    $edition = $editions[0] ?? null;
    if (!$edition || $edition->post_name !== $slug || $edition->post_password !== '') {
        status_header(404);
        nocache_headers();
        exit;
    }

    $canonical = 'https://udo.guide/editions/' . $match[1] . '/' . $match[2] . '/';
    status_header(200);
    header('Content-Type: text/html; charset=UTF-8');
    nocache_headers();
    if ($method === 'HEAD') {
        exit;
    }

    // Render only the reviewed HTML. WordPress content filters can run shortcodes and embeds.
    $title = esc_html($edition->post_title);
    $canonical_url = esc_url($canonical);
    $content = wp_kses_post($edition->post_content);
    echo '<!doctype html><html lang="' . esc_attr(get_bloginfo('language')) . '"><head>';
    echo '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">';
    echo '<title>' . $title . '</title><link rel="canonical" href="' . $canonical_url . '">';
    echo '</head><body><main><h1>' . $title . '</h1>' . $content . '</main></body></html>';
    exit;
}, 0);
