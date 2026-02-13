<?php

namespace App\Filament\Resources\PostResource\Pages;

use App\Filament\Resources\PostResource;
use Filament\Actions;
use Filament\Resources\Pages\CreateRecord;

class CreatePost extends CreateRecord
{
    protected static string $resource = PostResource::class;

    protected function mutateFormDataBeforeCreate(array $data): array
    {
        $data['user_id'] = auth()->id();
        
        if ($tenant = \Filament\Facades\Filament::getTenant()) {
            $data['tenant_id'] = $tenant->id;
        }

        return $data;
    }

    protected function getRedirectUrl(): string
    {
        \Illuminate\Support\Facades\Log::info('Redirecting from CreatePost to index');
        return $this->getResource()::getUrl('index');
    }
}
