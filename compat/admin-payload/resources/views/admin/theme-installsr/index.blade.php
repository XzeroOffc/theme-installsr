@extends('layouts.admin')
@section('title', 'Pengaturan Tema')
@section('content-header')
<h1>Pengaturan Tema <small>{{ $themeName }}</small></h1>
<ol class="breadcrumb"><li><a href="{{ route('admin.index') }}">Admin</a></li><li class="active">Pengaturan Tema</li></ol>
@endsection
@section('content')
@if(session('theme_saved'))
<div class="alert alert-success" role="status">Pengaturan tersimpan. Muat ulang dashboard untuk melihat perubahan.</div>
@endif
@if($errors->any())
<div class="alert alert-danger" role="alert"><strong>Pengaturan belum disimpan.</strong><ul>@foreach($errors->all() as $error)<li>{{ $error }}</li>@endforeach</ul></div>
@endif
<form method="POST" action="{{ route('admin.theme-installsr.update') }}">
{{ csrf_field() }}
<input type="hidden" name="theme" value="{{ $themeName }}">
<div class="box"><div class="box-header with-border"><h2 class="box-title">Tautan komunitas</h2></div><div class="box-body">
<p>Tautan Chat Admin, Channel, dan Group akan muncul di dashboard. Pengaturan disimpan khusus untuk tema <strong>{{ $themeName }}</strong>.</p>
<div class="form-group"><label for="ti-heading">Judul bagian</label><input id="ti-heading" class="form-control" name="heading" maxlength="80" required value="{{ old('heading', $preferences['heading']) }}"></div>
<input type="hidden" name="enabled" value="0"><label><input type="checkbox" name="enabled" value="1" {{ old('enabled', $preferences['enabled']) ? 'checked' : '' }}> Tampilkan bagian komunitas</label>
</div></div>
@foreach(['admin' => 'Chat Admin', 'channel' => 'Channel', 'group' => 'Group'] as $key => $title)
<div class="box"><div class="box-header with-border"><h2 class="box-title">{{ $title }}</h2></div><div class="box-body">
<div class="form-group"><label for="ti-{{ $key }}-label">Nama yang tampil</label><input id="ti-{{ $key }}-label" class="form-control" name="links[{{ $key }}][label]" required maxlength="60" value="{{ old('links.'.$key.'.label', $preferences['links'][$key]['label']) }}"></div>
<div class="form-group"><label for="ti-{{ $key }}-description">Keterangan</label><input id="ti-{{ $key }}-description" class="form-control" name="links[{{ $key }}][description]" maxlength="160" value="{{ old('links.'.$key.'.description', $preferences['links'][$key]['description']) }}"></div>
<div class="form-group"><label for="ti-{{ $key }}-url">Tautan tujuan</label><input id="ti-{{ $key }}-url" class="form-control" name="links[{{ $key }}][url]" type="url" maxlength="2048" placeholder="https://" aria-describedby="ti-{{ $key }}-help" value="{{ old('links.'.$key.'.url', $preferences['links'][$key]['url']) }}"><p id="ti-{{ $key }}-help" class="help-block">Isi tautan lengkap. Jika kosong, tombol tidak ditampilkan.</p></div>
<input type="hidden" name="links[{{ $key }}][enabled]" value="0"><label><input type="checkbox" name="links[{{ $key }}][enabled]" value="1" {{ old('links.'.$key.'.enabled', $preferences['links'][$key]['enabled']) ? 'checked' : '' }}> Aktifkan {{ $title }}</label>
</div></div>
@endforeach
<button type="submit" class="btn btn-primary">Simpan pengaturan</button>
<a href="{{ url('/') }}" class="btn btn-default">Buka dashboard</a>
</form>
@endsection
