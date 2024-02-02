<script lang="ts">
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

  function submit(item: {role: string, content: string}[]) {
    dispatch('submit', item);
  }
</script>

<Card padding="none" class="max-w-full">
  <div class="p-4">
    <Label class="pb-2">Scripted Messages</Label>
    <Fileupload bind:files={files} accept=".json"/>
  </div>

  <ol class="max-h-[40ch] overflow-y-auto">
    {#each data as item}
      <li
      class="py-2 px-4 border-b max-w-full hover:bg-primary-600/30 flex items-center gap-4"
      on:click={() => submit(item)}>
        {#each item as message}
          <div class="max-w-[20rem] overflow-hidden overflow-ellipsis whitespace-nowrap">
            <p class="text-xs font-bold text-gray-400">{message.role}</p>
            <p>{message.content}</p>
          </div>
        {/each}
    </li>
    {/each}
  </ol>
</Card>