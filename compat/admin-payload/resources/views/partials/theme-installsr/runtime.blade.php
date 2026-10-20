@php
    $themePreferences = \Pterodactyl\Services\ThemeInstallerSettings::get();
    $themePreferences['theme'] = \Pterodactyl\Services\ThemeInstallerSettings::active();
    $themePreferences['owner'] = (int) Auth::id() === 1;
@endphp
<script>window.ThemeInstallerSettings = {!! json_encode($themePreferences, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) !!};</script>
<link rel="stylesheet" href="{{ asset('themes/theme-installsr/community.css') }}?v=4">
