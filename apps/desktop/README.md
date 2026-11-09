# Desktop Application

This directory is reserved for the PyDoctor React + TypeScript desktop interface and its Tauri shell.

## Status

The application skeleton has not been generated yet. The required toolchain is currently unavailable:

- Node.js and npm are not installed.
- Rust, Cargo, and the Tauri CLI are not installed.
- Microsoft C++ Build Tools and WebView2 are Tauri prerequisites and have not been verified.

## Official Scaffold Path

When the prerequisites are installed, use the official Tauri 2 `create-tauri-app` utility. From this directory, the documented npm command is:

```powershell
npm create tauri-app@latest .
```

Select the React template, TypeScript flavor, and npm package manager. Review the generated configuration and versions rather than assuming them. The generated app must remain inside `apps/desktop`.

The Python engine lives separately in `engine/python` and must not be embedded into the desktop frontend.
