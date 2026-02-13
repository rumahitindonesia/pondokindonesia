<?php

namespace App\Filament\Resources\CampaignResource\Pages;

use App\Filament\Resources\CampaignResource;
use Filament\Actions;
use Filament\Resources\Pages\CreateRecord;

class CreateCampaign extends CreateRecord
{
    protected static string $resource = CampaignResource::class;

    protected function beforeCreate(): void
    {
        $tenant = auth()->user()->latestTenant;
        if ($tenant && !$tenant->isPremium()) {
            $activeCount = $tenant->campaigns()->where('status', 'active')->count();
            if ($activeCount >= 1 && $this->data['status'] === 'active') {
                \Filament\Notifications\Notification::make()
                    ->title('Plan Limit Reached')
                    ->body('Free plan users can only have 1 active campaign at a time.')
                    ->danger()
                    ->send();

                $this->halt();
            }
        }
    }
}
