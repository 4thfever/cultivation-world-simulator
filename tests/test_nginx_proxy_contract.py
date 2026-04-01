from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_nginx_has_spa_fallback_for_root_route():
    nginx_conf = (get_project_root() / "deploy" / "nginx.conf").read_text(encoding="utf-8")

    assert "location / {" in nginx_conf
    assert "try_files $uri $uri/ /index.html;" in nginx_conf


def test_nginx_proxies_api_ws_and_assets_to_backend():
    nginx_conf = (get_project_root() / "deploy" / "nginx.conf").read_text(encoding="utf-8")

    assert "location /api" in nginx_conf
    assert "location /ws" in nginx_conf
    assert "location /assets" in nginx_conf
    assert nginx_conf.count("proxy_pass http://backend:8002;") >= 3


def test_nginx_ws_block_keeps_upgrade_headers():
    nginx_conf = (get_project_root() / "deploy" / "nginx.conf").read_text(encoding="utf-8")

    assert "location /ws" in nginx_conf
    assert "proxy_http_version 1.1;" in nginx_conf
    assert "proxy_set_header Upgrade $http_upgrade;" in nginx_conf
    assert 'proxy_set_header Connection "upgrade";' in nginx_conf
