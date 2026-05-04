import { type NextRequest, NextResponse } from "next/server";

const PROTECTED_PREFIXES = [
  "/datasets",
  "/eda",
  "/preprocessing",
  "/ml",
  "/chat",
];
const AUTH_PREFIXES = ["/login", "/register"];
const TOKEN_COOKIE = "ezidatic_token";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get(TOKEN_COOKIE)?.value;

  const isProtected = PROTECTED_PREFIXES.some((p) => pathname.startsWith(p));
  const isAuthRoute = AUTH_PREFIXES.some((p) => pathname.startsWith(p));

  if (isProtected && !token) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("from", pathname);
    return NextResponse.redirect(url);
  }

  if (isAuthRoute && token) {
    const url = request.nextUrl.clone();
    url.pathname = "/datasets";
    url.search = "";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /**
     * Run on every request except static assets / Next internals / API
     * proxy. Patterns must be literal — Next 14 doesn't support runtime
     * regex in `matcher`.
     */
    "/((?!_next/static|_next/image|favicon.ico|api).*)",
  ],
};
