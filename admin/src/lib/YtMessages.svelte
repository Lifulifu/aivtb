<script lang="ts">
  import { Card, Input, Button, ButtonGroup, Label, Toggle, Select } from 'flowbite-svelte'
  import { onDestroy, tick, createEventDispatcher, onMount } from 'svelte';
  import { scrollToBottom } from './util';
  import type { YtCommentItem } from './types';
  import Icon from '@iconify/svelte';

<<<<<<< HEAD
  const PING_INTERVAL_MS = 2000;

=======
  let videoUrl: string = '';
>>>>>>> 5e3b3c334a95662c97c747a9f3200b1f03c12e23
  let ytComments: YtCommentItem[] = [];
  let ytCommentsWs: WebSocket;
  let ytCommentsDom: any = null;
  let liveStreams: {id: string, title: string, liveChatId: string}[] = [];
  let liveChatId: string = '';
  let autoScroll: boolean = true;
  let pingInterval: any;

<<<<<<< HEAD
  const ytLiveStreamsUrl = 'http://localhost:8000/yt_live_streams';
  const ytCommentsUrl = 'ws://localhost:8000/yt_live_chat';
=======
  const dummyComment: YtCommentItem = { name: 'test', message: 'test test', time: '' };
  const ytCommentsUrl = 'ws://localhost:8000/yt_comments';
>>>>>>> 5e3b3c334a95662c97c747a9f3200b1f03c12e23
  const dispatch = createEventDispatcher();

  onMount(async () => {
    const res = await fetch(ytLiveStreamsUrl);
    try {
      const jsonRes = await res.json();
      liveStreams = jsonRes.map((item: any) => ({
        id: item.id,
        title: item.snippet.title,
        liveChatId: item.snippet.liveChatId
      }));
    } catch (e) {
      console.error(e);
      liveStreams = [];
    }
  });

  onDestroy(() => {
    ytCommentsWs?.close();
    clearInterval(pingInterval);
  })

  $: if (ytCommentsDom && autoScroll && ytComments) autoScrollYtComments()

  async function connectYtComments() {
    ytCommentsWs?.close();
    clearInterval(pingInterval);

    ytCommentsWs = new WebSocket(`${ytCommentsUrl}/${liveChatId}`);
    ytCommentsWs.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if(data) {
          const comments = data.map((item: any) => ({
            name: item.authorDetails.displayName,
            message: item.snippet.displayMessage
          }));
          ytComments = [...ytComments, ...comments];
        }
      } catch (e) {
        console.error(e)
      }
    }
    ytCommentsWs.onerror = (e) => {
      console.error(e)
    }

    pingInterval = setInterval(() => {
      if (ytCommentsWs.readyState === 1) {
        ytCommentsWs.send('ping');
      }
    }, PING_INTERVAL_MS)
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
<<<<<<< HEAD
=======
    <Input bind:value={videoUrl}/>
>>>>>>> 5e3b3c334a95662c97c747a9f3200b1f03c12e23
    <div class="w-full flex gap-2 items-center">
      <Select bind:value={liveChatId}>
        {#each liveStreams as liveStream}
          <option value={liveStream.liveChatId}>
            {liveStream.title} ({liveStream.id})
          </option>
        {/each}
      </Select>
      <ButtonGroup>
        <Button size="xs" color='alternative' on:click={disconnectYtComments}>Disconnect</Button>
        <Button size="xs" color='primary' on:click={connectYtComments}>Connect</Button>
      </ButtonGroup>
    </div>
    <div class="w-full flex gap-2 items-center">
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