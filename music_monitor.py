"""Read-only Windows media status. No audio capture or playback commands."""
import asyncio
from PySide6.QtCore import QThread, Signal


class MusicMonitor(QThread):
    changed=Signal(bool)
    error=Signal(str)

    def run(self):
        try: asyncio.run(self.watch())
        except Exception as exc:
            self.changed.emit(False); self.error.emit(f'Detecção de música indisponível: {exc}')

    async def watch(self):
        from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as Manager
        from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionPlaybackStatus as Status
        from winrt.windows.media import MediaPlaybackType
        manager=await Manager.request_async(); previous=None
        while not self.isInterruptionRequested():
            playing=False
            for session in manager.get_sessions():
                try:
                    info=session.get_playback_info()
                    if info.playback_status!=Status.PLAYING: continue
                    source=session.source_app_user_model_id.lower()
                    music_app=any(name in source for name in ('spotify','music','deezer','tidal','foobar','aimp','winamp'))
                    if info.playback_type==MediaPlaybackType.MUSIC or (music_app and info.playback_type!=MediaPlaybackType.VIDEO):
                        playing=True; break
                except OSError: continue
            if playing!=previous: self.changed.emit(playing); previous=playing
            await asyncio.sleep(1.5)
