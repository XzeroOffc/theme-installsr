<?php

namespace Pterodactyl\Http\Controllers\Admin;

use Illuminate\Http\Request;
use Illuminate\Validation\Rule;
use Pterodactyl\Http\Controllers\Controller;
use Pterodactyl\Services\ThemeInstallerSettings;

final class ThemeInstallerController extends Controller
{
    private function owner(Request $request): void
    {
        abort_unless((int) $request->user()?->id === 1, 403);
    }

    public function index(Request $request)
    {
        $this->owner($request);
        return view('admin.theme-installsr.index', [
            'themeName' => ThemeInstallerSettings::active(),
            'preferences' => ThemeInstallerSettings::get(),
        ]);
    }

    public function update(Request $request)
    {
        $this->owner($request);
        $rules = [
            'theme' => ['required', Rule::in([ThemeInstallerSettings::active()])],
            'heading' => ['required', 'string', 'max:80'],
            'enabled' => ['required', 'boolean'],
        ];
        foreach (['admin', 'channel', 'group'] as $key) {
            $rules["links.$key.label"] = ['required', 'string', 'max:60'];
            $rules["links.$key.description"] = ['nullable', 'string', 'max:160'];
            $rules["links.$key.enabled"] = ['required', 'boolean'];
            $rules["links.$key.url"] = ['nullable', 'string', 'max:2048', 'url', function ($attribute, $value, $fail) {
                if (!in_array(strtolower((string) parse_url($value, PHP_URL_SCHEME)), ['http', 'https'], true)) {
                    $fail('Gunakan tautan lengkap dengan https:// atau http://.');
                }
            }];
        }
        $validated = $request->validate($rules);
        $data = ['heading' => $validated['heading'], 'enabled' => $request->boolean('enabled'), 'links' => []];
        foreach (['admin', 'channel', 'group'] as $key) {
            $link = $validated['links'][$key];
            $data['links'][$key] = [
                'label' => $link['label'], 'description' => $link['description'] ?? '',
                'url' => $link['url'] ?? '', 'enabled' => $request->boolean("links.$key.enabled"),
            ];
        }
        ThemeInstallerSettings::save($data);
        return redirect()->route('admin.theme-installsr')->with('theme_saved', true);
    }
}
