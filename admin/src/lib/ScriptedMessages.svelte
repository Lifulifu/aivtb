<script lang="ts">
  import Icon from '@iconify/svelte';
import { Button, Card, Fileupload, Label } from 'flowbite-svelte'
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  export let data: {role: string, content: string}[][] = [];
  let files: FileList;

  $: if (files && files.length > 0) {
    const file = files[0];
    const reader = new FileReader();
    reader.onload = function(e) {
      const content = reader.result as string;
      try {
        data = JSON.parse(content);
      } catch (e) {
        console.error(e);
      }
    }
    reader.readAsText(file);
  }

  function sendItem(item: {role: string, content: string}[]) {
    dispatch('send', item);
  }

  function addItem(item: {role: string, content: string}[]) {
    dispatch('add', item);
  }
</script>

<Card padding="none" class="max-w-full">
  <div class="p-4">
    <Label class="pb-2">Scripted Messages</Label>
    <Fileupload bind:files={files} accept=".json"/>
  </div>

  <ol class="max-h-[80ch] overflow-y-auto">
    {#each data as item}
      <li
      class="group relative py-2 px-4 border-b max-w-full hover:bg-primary-600/30 flex items-center gap-4">
        {#each item as message}
          <div class="w-[10rem] overflow-hidden overflow-ellipsis whitespace-nowrap flex-shrink-0">
            <p class="text-xs font-bold text-gray-400">{message.role}</p>
            <p>{message.content}</p>
          </div>
        {/each}
        <div class="gap-1 absolute hidden group-hover:flex right-2 top-2">
          <Button color="alternative" class="p-2" on:click={() => sendItem(item)}><Icon icon="material-symbols:arrow-forward"/></Button>
          <Button color="alternative" class="p-2" on:click={() => addItem(item)}><Icon icon="material-symbols:add"/></Button>
        </div>
    </li>
    {/each}
  </ol>
</Card>