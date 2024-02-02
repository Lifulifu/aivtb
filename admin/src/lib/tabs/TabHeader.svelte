<script>
	import { getContext } from 'svelte';
	import { TABS } from './Tabs.svelte';

	const tab = {};
	const { registerTab, selectTab, selectedTab } = getContext(TABS);

	registerTab(tab);

  export let inactiveClass = 'font-medium border-b-[3px] text-gray-500 border-transparent hover:border-gray-200';
  export let activeClass = 'font-medium border-b-[3px] text-primary-600 border-primary-600';
  $: resultClass = $selectedTab === tab ? activeClass : inactiveClass;
</script>

<button class="py-2 px-4 rounded-t-md {resultClass} {$$props.class}" on:click={() => selectTab(tab)}>
	<slot></slot>
</button>