#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_network::init())
        .plugin(tauri_plugin_autostart::init(tauri_plugin_autostart::MacosLauncher::LaunchAgent, Some(vec![])))
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            #[cfg(desktop)]
            {
                use tauri::menu::{Menu, MenuItem, PredefinedMenuItem};
                use tauri::tray::{TrayIconBuilder};
                use tauri::Manager;
                use tauri_plugin_shell::ShellExt;
                use tauri_plugin_shell::process::CommandEvent;

                // Spawn the Python Backend Sidecar
                let sidecar = app.shell().sidecar("backend").expect("failed to create `backend` binary command");
                let (mut rx, _child) = sidecar.spawn().expect("Failed to spawn sidecar");

                tauri::async_runtime::spawn(async move {
                    while let Some(event) = rx.recv().await {
                        if let CommandEvent::Stdout(line) = event {
                            println!("[Python] {}", String::from_utf8_lossy(&line));
                        } else if let CommandEvent::Stderr(line) = event {
                            eprintln!("[Python Error] {}", String::from_utf8_lossy(&line));
                        }
                    }
                });

                let show_i = MenuItem::with_id(app, "show", "Show Main App", true, None::<&str>)?;
                let pause_i = MenuItem::with_id(app, "pause", "Pause Sync", true, None::<&str>)?;
                let settings_i =
                    MenuItem::with_id(app, "settings", "Settings", true, None::<&str>)?;
                let quit_i = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;

                let menu = Menu::with_items(
                    app,
                    &[
                        &show_i,
                        &pause_i,
                        &PredefinedMenuItem::separator(app)?,
                        &settings_i,
                        &PredefinedMenuItem::separator(app)?,
                        &quit_i,
                    ],
                )?;

                let _tray = TrayIconBuilder::new()
                    .icon(app.default_window_icon().unwrap().clone())
                    .menu(&menu)
                    .show_menu_on_left_click(false)
                    .on_menu_event(|app, event| match event.id.as_ref() {
                        "quit" => {
                            std::process::exit(0);
                        }
                        "show" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                        _ => {}
                    })
                    .build(app)?;
            }

            if cfg!(debug_assertions) {
                app.handle().plugin(
                    tauri_plugin_log::Builder::default()
                        .level(log::LevelFilter::Info)
                        .build(),
                )?;
            }

            app.handle()
                .plugin(tauri_plugin_global_shortcut::Builder::new().build())?;

            Ok(())
        })
        .on_window_event(|window, event| match event {
            tauri::WindowEvent::CloseRequested { api, .. } => {
                // Prevent window from closing
                api.prevent_close();
                // Hide the window instead
                let _ = window.hide();
            }
            _ => {}
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
