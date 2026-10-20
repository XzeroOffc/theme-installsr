<style>
:root {
@foreach(\Pterodactyl\Services\ThemeInstallerSettings::palette() as $name => $color)
    --ti-{{ $name }}: {{ $color }};
@endforeach
}
</style>
<link rel="stylesheet" href="{{ asset('themes/theme-installsr/admin.css') }}?v=4">
