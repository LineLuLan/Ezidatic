/**
 * Visually-hidden skip link that becomes visible on keyboard focus.
 * First focusable element in the body so screen-reader and keyboard
 * users can jump straight to `<main id="content">`.
 */
export function SkipToContent() {
  return (
    <a
      href="#content"
      className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded-md focus:bg-background focus:px-3 focus:py-2 focus:text-sm focus:font-medium focus:text-foreground focus:shadow-md focus:ring-2 focus:ring-ring"
    >
      Skip to content
    </a>
  );
}
