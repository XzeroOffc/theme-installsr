<?php

namespace Pterodactyl\Services;

use Illuminate\Support\Facades\File;

final class ThemeInstallerSettings
{
    public static function active(): string
    {
        return (string) config('theme-installsr.active', 'default');
    }

    public static function palette(): array
    {
        $palette = config('theme-installsr.palette', []);
        $theme = self::active();
        $table = $theme === 'elysium' ? 'elysium' : ($theme === 'stellar' ? 'theme' : null);
        if ($table && \Illuminate\Support\Facades\Schema::hasTable($table)) {
            $row = \Illuminate\Support\Facades\DB::table($table)->first();
            $fields = $theme === 'elysium'
                ? ['bg' => 'color_1', 'panel' => 'color_3', 'accent' => 'color_meta']
                : ['bg' => 'background', 'panel' => 'input', 'accent' => 'primaryhover'];
            foreach ($fields as $key => $column) {
                $color = $row?->$column;
                if (is_string($color) && preg_match('/^#[0-9a-fA-F]{6}$/D', $color)) {
                    $palette[$key] = $color;
                }
            }
        }
        $palette['text'] = self::foreground($palette['panel']);
        $palette['bg-text'] = self::foreground($palette['bg']);
        $palette['muted'] = $palette['text'];
        $palette['accent-text'] = self::foreground($palette['accent']);
        return $palette;
    }

    private static function foreground(string $hex): string
    {
        $channels = array_map(static function ($part) {
            $value = hexdec($part) / 255;
            return $value <= 0.04045 ? $value / 12.92 : pow(($value + 0.055) / 1.055, 2.4);
        }, str_split(substr($hex, 1), 2));
        $luminance = $channels[0] * 0.2126 + $channels[1] * 0.7152 + $channels[2] * 0.0722;
        return 1.05 / ($luminance + 0.05) >= ($luminance + 0.05) / 0.05 ? '#ffffff' : '#000000';
    }

    public static function get(): array
    {
        $path = storage_path('app/theme-installsr/preferences.json');
        $stored = is_file($path) ? json_decode(File::get($path), true) : [];
        $stored = is_array($stored) ? ($stored[self::active()] ?? []) : [];
        $defaults = ['heading' => 'Sosial Media Admin', 'enabled' => true, 'links' => []];
        foreach (['admin' => 'Kontak Admin', 'channel' => 'Channel', 'group' => 'Group'] as $key => $label) {
            $defaults['links'][$key] = ['label' => $label, 'description' => '', 'url' => '', 'enabled' => true];
        }
        return array_replace_recursive($defaults, is_array($stored) ? $stored : []);
    }

    public static function save(array $data): void
    {
        $directory = storage_path('app/theme-installsr');
        File::ensureDirectoryExists($directory, 0750);
        $path = $directory . '/preferences.json';
        $stored = is_file($path) ? json_decode(File::get($path), true) : [];
        $stored = is_array($stored) ? $stored : [];
        $stored[self::active()] = $data;
        File::replace($path, json_encode($stored, JSON_THROW_ON_ERROR | JSON_PRETTY_PRINT), 0640);
    }
}
