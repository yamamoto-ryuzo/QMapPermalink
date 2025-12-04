# -*- coding: utf-8 -*-
"""Shared lightweight HTTP utilities for QMapPermalink.

This module provides minimal request/response helpers used by the
plugin's internal socket-based HTTP servers. Keeping these utilities
centralized makes future extensions (middleware, logging, CORS, etc.)
easier.
"""
import socket


def read_http_request(conn, max_size=8192):
    """Read raw HTTP request bytes from a connected socket.

    Args:
        conn: socket-like object with recv
        max_size: maximum bytes to read (prevents unbounded memory use)

    Returns:
        bytes: raw request bytes (may be empty on error/timeout)
    """
    try:
        data = b''
        while b'\r\n\r\n' not in data and len(data) < max_size:
            chunk = conn.recv(1024)
            if not chunk:
                break
            data += chunk
        return data
    except Exception:
        return b''


def send_http_response(conn, status_code, reason, body, content_type="text/plain; charset=utf-8"):
    """Send a minimal HTTP response (text or bytes).

    Args:
        conn: socket-like object with sendall
        status_code: integer HTTP status code
        reason: status reason phrase
        body: str or bytes body
        content_type: Content-Type header value
    """
    try:
        if isinstance(body, str):
            body_bytes = body.encode('utf-8')
        else:
            body_bytes = body or b''

        header_lines = [
            f"HTTP/1.1 {status_code} {reason}",
            f"Content-Length: {len(body_bytes)}",
            f"Content-Type: {content_type}",
            "Access-Control-Allow-Origin: *",
            "Connection: close",
            "",
            "",
        ]
        header = "\r\n".join(header_lines).encode('utf-8')
        conn.sendall(header + body_bytes)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


def send_xml_response(conn, xml_content):
    """Send a 200 OK XML response encoded as UTF-8."""
    try:
        xml_bytes = xml_content.encode('utf-8')
        header_lines = [
            "HTTP/1.1 200 OK",
            f"Content-Length: {len(xml_bytes)}",
            "Content-Type: text/xml; charset=utf-8",
            "Access-Control-Allow-Origin: *",
            "Connection: close",
            "",
            "",
        ]
        header = "\r\n".join(header_lines).encode('utf-8')
        conn.sendall(header + xml_bytes)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


def send_binary_response(conn, status_code, reason, data, content_type):
    """Send a binary HTTP response (images, etc.)."""
    try:
        header_lines = [
            f"HTTP/1.1 {status_code} {reason}",
            f"Content-Length: {len(data)}",
            f"Content-Type: {content_type}",
            "Access-Control-Allow-Origin: *",
            "Connection: close",
            "",
            "",
        ]
        header = "\r\n".join(header_lines).encode('utf-8')
        conn.sendall(header + data)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


def send_wms_error_response(conn, error_code, error_message):
        """Send an OWS-style ExceptionReport XML response for WMS errors.

        Use the OWS ExceptionReport structure (namespace http://www.opengis.net/ows)
        which is widely accepted across OGC services (WMS/WFS/etc.). This function
        sends an HTTP 400 response by default and sets a proper XML content-type.
        """
        try:
                # Build an OWS ExceptionReport which is more interoperable than the
                # legacy ServiceExceptionReport used by some older servers.
                xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<ExceptionReport version="1.3.0" xmlns="http://www.opengis.net/ows">
    <Exception exceptionCode="{error_code}">
        <ExceptionText>{error_message}</ExceptionText>
    </Exception>
</ExceptionReport>"""
                # Use a 400 Bad Request for parameter/usage errors; callers may choose
                # to send a different status via send_http_response if appropriate.
                send_http_response(conn, 400, "Bad Request", xml_content, content_type="text/xml; charset=utf-8")
        except Exception:
                # Fallback to plain text response if XML assembly fails
                send_http_response(conn, 500, "Internal Server Error", f"{error_code}: {error_message}")


def send_wfs_error_response(conn, error_code, error_message, locator=None):
        """Send a basic WFS/OWS-style ExceptionReport XML response.

        This generates a small OWS/ExceptionReport-style XML which is commonly
        used by OGC services (WFS/WMS/etc.) to report parameter and request
        errors to clients.
        """
        try:
                locator_attr = f' locator="{locator}"' if locator else ''
                xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<ExceptionReport version="1.0.0" xmlns="http://www.opengis.net/ows">
    <Exception exceptionCode="{error_code}"{locator_attr}>
        <ExceptionText>{error_message}</ExceptionText>
    </Exception>
</ExceptionReport>"""
                send_xml_response(conn, xml_content)
        except Exception:
                # Fallback to plain text response if XML assembly fails
                send_http_response(conn, 500, "Internal Server Error", f"{error_code}: {error_message}")
