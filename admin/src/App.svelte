<script lang="ts">
  import { Button, ButtonGroup, Card, Dropdown, DropdownItem, Input, Spinner, Toast, Modal, Textarea, NumberInput, Label, Toggle } from 'flowbite-svelte'
  import { onDestroy, onMount, tick } from 'svelte';
  import { fade } from 'svelte/transition';
  import { scrollToBottom } from './lib/util';
  import Icon from '@iconify/svelte';

  let userQuestion: string = '';
  let showUserQuestionModal: boolean = false;
  let temperature: number = 0.7;

  let messagePreview: {role: string, content: string}[] = [];
  let messagePreviewWs: WebSocket;
  let messagePreviewError: boolean = false;
  let isLoading: boolean = false;
  let playbackDeviceId: number = -1;
  $: canPublishMessage = messagePreview?.length >= 1 && messagePreview[messagePreview.length - 1].role === 'assistant';
  let edittingMessage: any = null;

  let videoId: string = '';
  type YtCommentItem = {name: string, message: string, time: string}
  let ytComments: YtCommentItem[] = [];
  let ytCommentsWs: WebSocket;
  let ytCommentsDom: any = null;
  let ytCommentsError: boolean = false;
  let autoScroll: boolean = true;

  let subtitle: string = '';
  let subtitleWs: WebSocket;
  let subtitleError: boolean = false;

  const sendMessageUrl = 'http://localhost:8000/send_message';
  const publishMessageUrl = 'http://localhost:8000/publish_message';
  const previewMessageeUrl = 'ws://localhost:8000/preview_message';
  const ytCommentsUrl = 'ws://localhost:8000/yt_comments';
  const subtitleUrl = 'ws://localhost:8000/subtitle';

  onMount(() => {
    connectMessagePreview();
    connectSubtitle();
  })

  onDestroy(() => {
    messagePreviewWs.close();
    ytCommentsWs.close();
  })

  $: if (ytCommentsDom && autoScroll && ytComments) autoScrollYtComments()

  async function autoScrollYtComments() {
    await tick();
    scrollToBottom(ytCommentsDom);
  }

  async function connectMessagePreview() {
    if (messagePreviewWs) messagePreviewWs.close();
    messagePreviewWs = new WebSocket(previewMessageeUrl);
    messagePreviewWs.onmessage = (e) => {
      isLoading = false;
      messagePreviewError = false;
      try {
        const data = JSON.parse(e.data)
        if(data) messagePreview = data;
      } catch (e) {
        messagePreview = []
      }
    }
    messagePreviewWs.onerror = (e) => {
      console.error(e)
      messagePreviewError = true;
    }
  }

  async function connectYtComments() {
    if (!videoId) return;
    if (ytCommentsWs) ytCommentsWs.close();
    ytCommentsWs = new WebSocket(`${ytCommentsUrl}/${videoId}`);
    ytCommentsWs.onmessage = (e) => {
      ytCommentsError = false;
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
      ytCommentsError = true;
    }
  }

  async function connectSubtitle() {
    if (subtitleWs) subtitleWs.close();
    subtitleWs = new WebSocket(subtitleUrl);
    subtitleWs.onmessage = (e) => {
      subtitleError = false;
      try {
        const data = JSON.parse(e.data)
        if(data) {
          subtitle = subtitle + '\n' + data;
        }
      } catch (e) {
        console.log(e)
      }
    }
    subtitleWs.onerror = (e) => {
      console.error(e)
      subtitleError = true;
    }
  }

  async function sendMessage(message: string = '') {
    isLoading = true;
    const messages = message ? [...messagePreview, { role: "user", content: message }] : messagePreview;
    await fetch(sendMessageUrl, {
      method: 'post',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: messages,
        temperature: temperature
      })
    }).catch(e => {
      console.error(e)
    })
  }

  function addEmptyMessage(role: 'assistant'|'user' = 'assistant') {
    const message = {role, content: ''};
    edittingMessage = message;
    messagePreview = [...messagePreview, message];
  }

  async function onInputSubmit() {
    await sendMessage(userQuestion);
    userQuestion = ''
  }

  async function onInputClearAndSend() {
    messagePreview = [];
    await sendMessage(userQuestion);
    userQuestion = '';
  }

  async function onYtCommentClick(commentItem: YtCommentItem) {
    userQuestion = commentItem.message;
  }

  async function publishMessage() {
    if (!canPublishMessage) return;
    const q = messagePreview[messagePreview.length - 2].content;
    const a = messagePreview[messagePreview.length - 1].content;
    await fetch(publishMessageUrl, {
      method: 'post',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ q, a, device: playbackDeviceId })
    }).catch(e => {
      console.error(e)
    })
  }

  function deleteMessage(message: any) {
    messagePreview = messagePreview.filter((r) => r !== message);
  }

  function regenerateMessage(message: any) {
    const _messagePreview = []
    // delete all messages after response
    for(let res of messagePreview) {
      if (res === message) break;
      _messagePreview.push(res);
    }
    messagePreview = _messagePreview;
    sendMessage();
  }

  $: console.log(messagePreview)
</script>

<main>
  <div class="container w-full mt-8 space-y-4 lg:grid grid-cols-2 items-start gap-4">
    <!-- yt comments -->
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

    <div class="">
    <!-- user message input -->
      <form class="space-y-2" on:submit|preventDefault={onInputSubmit}>
        <div class="flex gap-2">
          <Button color="alternative"
            on:click={() => sendMessage('<instruction>自我介紹')}>自我介紹</Button>
          <Button color="alternative"
            on:click={() => sendMessage('<instruction>雜談')}>雜談</Button>
          <Button color="alternative"
            on:click={() => sendMessage('<instruction>繼續')}>繼續</Button>
        </div>

        <div class="w-full flex gap-2">
          <Input class="flex-grow" bind:value={userQuestion}/>
          <Button color="alternative" class="p-2" on:click={() => showUserQuestionModal = true}>
            <Icon icon="mdi:magnify-scan" height={20}/>
          </Button>
        </div>
        <div class="flex items-end gap-2 w-full">
          <Label class="flex-grow">
            Temperature
            <NumberInput bind:value={temperature} min={0.1} max={2.0} step={0.05}/>
          </Label>
          <Button type="submit" class="flex-grow" color="primary">Send</Button>
          <Button class="flex-grow" color="primary" on:click={onInputClearAndSend}>Clear & Send</Button>
        </div>
      </form>

      <!-- QA streaming display -->
      <Card class="mt-8 max-w-full space-y-2 bg-gray-200" padding="md">
        <div class="flex gap-2">
          <ButtonGroup>
            <Button color='alternative' on:click={() => messagePreviewWs.close()}>Disconnect</Button>
            <Button color='primary' on:click={connectMessagePreview}>Connect</Button>
          </ButtonGroup>
          <Button class="ml-auto" color="primary" on:click={() => addEmptyMessage('user')}>Add User</Button>
          <Button color="primary" on:click={() => addEmptyMessage('assistant')}>Add Ai</Button>
          <Button color="alternative" on:click={() => messagePreview = []}>Clear</Button>
        </div>
        {#if isLoading}
          <div class="flex justify-center">
            <Spinner/>
          </div>
        {:else}
          {#each messagePreview as message}
            <Card class="max-w-full" padding="md">
              <div class="flex gap-2 items-center">
                <div class="flex-grow">
                  <p on:click={() => edittingMessage = message} class="text-xs font-bold text-gray-400">{message.role}</p>
                  {#if message === edittingMessage}
                    <Textarea class="mr-2 text-lg" bind:value={message.content}/>
                  {:else}
                    <p on:click={() => edittingMessage = message}>{message.content}</p>
                  {/if}
                </div>
                <div class="flex">
                  {#if message === edittingMessage}
                    <button class="p-2 rounded-full hover:bg-gray-200" on:click={() => edittingMessage = null}><Icon icon="material-symbols:close-small-rounded"/></button>
                  {:else}
                    {#if message.role === 'assistant'}
                      <button class="p-2 rounded-full hover:bg-gray-200" on:click={() => regenerateMessage(message)}><Icon icon="material-symbols:refresh-rounded"/></button>
                    {/if}
                    <button class="p-2 text-red-700 rounded-full hover:bg-gray-200" on:click={() => deleteMessage(message)}><Icon icon="mdi:trash-outline"/></button>
                  {/if}
                </div>
              </div>
            </Card>
          {/each}
        {/if}
        <div class="flex items-end gap-2">
          <Label class="flex-grow">
            Playback device
            <NumberInput class='ml-auto' bind:value={playbackDeviceId}/>
          </Label>
          <Button color='primary' class="flex-grow" on:click={publishMessage} disabled={!canPublishMessage}>Publish</Button>
        </div>
      </Card>

      <!-- Subtitle display -->
      <Card class="mt-8 space-y-2 max-w-full">
        <div class="flex">
          <ButtonGroup>
            <Button color='alternative' on:click={() => subtitleWs.close()}>Disconnect</Button>
            <Button color='primary' on:click={connectSubtitle}>Connect</Button>
          </ButtonGroup>
          <Button class='ml-auto' color='alternative' on:click={() => subtitle = ''}>Clear</Button>
        </div>
        <p class="whitespace-pre-wrap">{subtitle}</p>
      </Card>
    </div>
  </div>
</main>

<Modal bind:open={showUserQuestionModal}>
  <h1>Message</h1>
  <Textarea bind:value={userQuestion}/>
</Modal>

{#if messagePreviewError}
  <Toast color="red" position="bottom-right" transition={fade}>
    <Icon slot="icon" icon="zondicons:close-outline"/>
    Cannot connect to AI response stream.
  </Toast>
{/if}

{#if ytCommentsError}
  <Toast color="red" position="bottom-right" transition={fade}>
    <Icon slot="icon" icon="zondicons:close-outline"/>
    Cannot connect to YouTube comments stream.
  </Toast>
{/if}