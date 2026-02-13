<?php

namespace App\Filament\Resources\CampaignResource\Widgets;

use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class CampaignAnalytics extends BaseWidget
{
    protected function getStats(): array
    {
        $campaigns = \App\Models\Campaign::all();
        
        $totalLeads = $campaigns->sum(fn ($c) => $c->total_leads);
        $totalRegistered = $campaigns->sum(fn ($c) => $c->registered_leads);
        $totalRevenue = $campaigns->sum(fn ($c) => $c->total_revenue);
        
        $avgConversion = $totalLeads > 0 
            ? round(($totalRegistered / $totalLeads) * 100, 2) 
            : 0;

        return [
            Stat::make('Total Leads', number_format($totalLeads))
                ->description('Across all campaigns')
                ->descriptionIcon('heroicon-m-users')
                ->color('success'),
            Stat::make('Conversion Rate', $avgConversion . '%')
                ->description('Average conversion')
                ->descriptionIcon('heroicon-m-arrow-trending-up')
                ->color('info'),
            Stat::make('Total Revenue', 'IDR ' . number_format($totalRevenue))
                ->description('From registration/education fees')
                ->descriptionIcon('heroicon-m-banknotes')
                ->color('primary'),
        ];
    }
}
