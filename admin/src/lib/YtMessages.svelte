<script lang="ts">
  import { Card, Input, Button, ButtonGroup, Label, Toggle } from 'flowbite-svelte'
  import { onDestroy, tick, createEventDispatcher } from 'svelte';
  import { scrollToBottom } from './util';
  import type { YtCommentItem } from './types';
  import Icon from '@iconify/svelte';

  let videoUrl: string = '';
  let ytComments: YtCommentItem[] = [];
  let ytCommentsWs: WebSocket;
  let ytCommentsDom: any = null;
  let autoScroll: boolean = true;
  let pingInterval: any;

  const dummyComment: YtCommentItem = { name: 'test', message: 'test test', time: '' };
  const ytCommentsUrl = 'ws://localhost:8000/yt_comments';
  const dispatch = createEventDispatcher();

  onDestroy(() => {
    ytCommentsWs?.close();
    clearInterval(pingInterval);
  })

  $: if (ytCommentsDom && autoScroll && ytComments) autoScrollYtComments()

  async function connectYtComments() {
    if (!videoUrl) return;

    ytCommentsWs?.close();
    clearInterval(pingInterval);

    const videoId = new URLSearchParams(videoUrl.split('?')?.[1]).get('v') ?? videoUrl;
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

    pingInterval = setInterval(() => {
      if (ytCommentsWs.readyState === 1) {
        ytCommentsWs.send('ping');
      }
    }, 1000)
  }

  function disconnectYtComments() {
    ytCommentsWs?.close();
    clearInterval(pingInterval);
  }

  async function autoScrollYtComments() {
    await tick();
    scrollToBottom(ytCommentsDom);
  }

  async function sendItem(commentItem: YtCommentItem) {
    dispatch('send', commentItem)
  }

  async function addItem(commentItem: YtCommentItem) {
    dispatch('add', commentItem)
  }

</script>

<Card class="max-w-full space-y-2 overflow-hidden" padding="none">
  <div class="w-full flex flex-col items-center gap-2 p-4">
    <Input bind:value={videoUrl}/>
    <div class="w-full flex gap-2 items-center">
      <ButtonGroup>
        <Button size="xs" color='alternative' on:click={disconnectYtComments}>Disconnect</Button>
        <Button size="xs" color='primary' on:click={connectYtComments}>Connect</Button>
      </ButtonGroup>
      <Label class='ml-auto'>auto scroll</Label>
      <Toggle bind:checked={autoScroll}/>
      <Button color='alternative' class="p-2" on:click={() => ytComments = [...ytComments, dummyComment]}>Test</Button>
      <Button color='alternative' class="p-2" on:click={() => ytComments = []}><Icon icon="ph:trash-bold"/></Button>
    </div>
  </div>
  <ol class="max-h-[40ch] overflow-y-auto" bind:this={ytCommentsDom}>
    {#each ytComments as item}
      <li class="group relative cursor-pointer py-2 px-4 border-b max-w-full hover:bg-primary-600/30 break-words">
        <p class="text-xs font-bold text-gray-400">{item.name}</p>
        <p>{item.message}</p>

        <div class="absolute hidden group-hover:flex top-2 right-2 gap-1">
          <Button color="alternative" class="p-2" on:click={() => sendItem(item)}><Icon icon="material-symbols:arrow-forward"/></Button>
          <Button color="alternative" class="p-2" on:click={() => addItem(item)}><Icon icon="material-symbols:add"/></Button>
        </div>
      </li>
    {/each}
  </ol>
</Card>