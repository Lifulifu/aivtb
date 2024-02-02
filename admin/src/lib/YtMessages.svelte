<script lang="ts">
  import { Card, Input, Button, ButtonGroup, Label, Toggle } from 'flowbite-svelte'
  import { onDestroy, tick, createEventDispatcher } from 'svelte';
  import { scrollToBottom } from './util';
  import type { YtCommentItem } from './types';

  let videoId: string = '';
  let ytComments: YtCommentItem[] = [];
  let ytCommentsWs: WebSocket;
  let ytCommentsDom: any = null;
  let autoScroll: boolean = true;

  const ytCommentsUrl = 'ws://localhost:8000/yt_comments';
  const dispatch = createEventDispatcher();

  onDestroy(() => {
    if (ytCommentsWs) {
      ytCommentsWs.close();
    }
  })

  $: if (ytCommentsDom && autoScroll && ytComments) autoScrollYtComments()

  async function connectYtComments() {
    if (!videoId) return;
    if (ytCommentsWs) ytCommentsWs.close();
    ytCommentsWs = new WebSocket(`${ytCommentsUrl}/${videoId}`);
    ytCommentsWs.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if(data) {
          ytComments.push(data);
          ytComments = ytComments;
        }
      } catch (e) {
        console.log(e)
      }
    }
    ytCommentsWs.onerror = (e) => {
      console.error(e)
    }
  }

  async function autoScrollYtComments() {
    await tick();
    scrollToBottom(ytCommentsDom);
  }

  async function onYtCommentClick(commentItem: YtCommentItem) {
    dispatch('submit', commentItem)
  }

</script>

<Card class="max-w-full space-y-2" padding="none">
  <div class="w-full flex flex-col items-center gap-2 p-4">
    <Input bind:value={videoId}/>
    <div class="w-full flex gap-2 items-center">
      <ButtonGroup>
        <Button color='alternative' on:click={() => ytCommentsWs.close()}>Disconnect</Button>
        <Button color='primary' on:click={connectYtComments}>Connect</Button>
      </ButtonGroup>
      <Label class='ml-auto'>auto scroll</Label>
      <Toggle bind:checked={autoScroll}/>
      <Button color='alternative' on:click={() => ytComments = []}>Clear</Button>
    </div>
  </div>
  <ol class="max-h-[40ch] overflow-y-auto" bind:this={ytCommentsDom}>
    {#each ytComments as item}
      <li class="cursor-pointer py-2 px-4 border-b max-w-full hover:bg-primary-600/30 break-words"
      on:click={() => onYtCommentClick(item)}>
        <p class="text-xs font-bold text-gray-400">{item.name}</p>
        <p>{item.message}</p>
      </li>
    {/each}
  </ol>
</Card>