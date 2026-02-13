@php
    $current = $getRecord()->current_amount;
    $target = $getRecord()->target_amount;
    $percent = $target > 0 ? ($current / $target) * 100 : 0;
    $percent = min($percent, 100);
@endphp

<div class="w-full space-y-1">
    <div class="flex justify-between text-xs mb-1">
        <span class="text-gray-500 dark:text-gray-400">Tercapai</span>
        <span class="font-medium text-primary-600 dark:text-primary-400">{{ number_format($percent, 0) }}%</span>
    </div>
    <div class="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700 overflow-hidden">
        <div class="bg-primary-600 h-2 rounded-full transition-all duration-500" style="width: {{ number_format($percent, 2) }}%"></div>
    </div>
</div>
