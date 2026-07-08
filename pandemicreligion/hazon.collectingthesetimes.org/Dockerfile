# syntax=docker/dockerfile:1
# Preview this flattened Pandemic Religion archive as a static site.
#   docker build -t pandemicreligion-preview .
#   docker run -d -p 8100:80 pandemicreligion-preview
# Files with a literal '?' in their names (Omeka S browse permutations, ?v=
# assets) serve fine: %3F in the request URL decodes to the on-disk '?'.
FROM caddy:alpine
COPY <<'EOF' /etc/caddy/Caddyfile
:80 {
	root * /usr/share/caddy
	file_server
}
EOF
COPY . /usr/share/caddy
