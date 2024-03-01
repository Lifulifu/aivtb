<script lang="ts">
  import { Button, ButtonGroup, Card, Input, Spinner, Toast, Modal, Textarea, NumberInput, Label, Select, Badge, Toggle } from 'flowbite-svelte'
  import { Tabs, TabList, TabBody, TabHeader } from './lib/tabs/tabs';
  import { onDestroy, onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  import Icon from '@iconify/svelte';

  import YtMessages from './lib/YtMessages.svelte';
  import type { YtCommentItem } from './lib/types';
  import ScriptedMessages from './lib/ScriptedMessages.svelte';

  let userQuestion: string = '';
  let showUserQuestionModal: boolean = false;
  let temperature: number = parseFloat(localStorage.getItem('temperature') ?? '0.7');
  $: localStorage.setItem('temperature', temperature.toString());

  let messagePreview: {role: string, content: string}[] = [];
  let messagePreviewWs: WebSocket;
  let messagePreviewError: boolean = false;
  let isLoading: boolean = false;
  $: canPublishMessage = messagePreview?.length >= 1 && messagePreview[messagePreview.length - 1].role === 'assistant';
  let edittingMessage: any = null;
  let audioDevices: {id: number, name: string}[] = [];
  let audioDevice: {id: number, name: string} = {id: -1, name: ''};
  $: if (audioDevice.name !== '') {
    localStorage.setItem('audioDevice', audioDevice.name);
  }

  let subtitles: string[] = [];
  let subtitleWs: WebSocket;
  let remainTasks: number = 0;

  const SERVER_URL = 'localhost:8000';
  const sendMessageUrl = `http://${SERVER_URL}/send_message`;
  const publishMessageUrl = `http://${SERVER_URL}/publish_message`;
  const previewMessageeUrl = `ws://${SERVER_URL}/preview_message`;
  const subtitleUrl = `ws://${SERVER_URL}/subtitle`;

  let automate: boolean = false;
  let includeHistory: number = 5;
  let idleActionTimer: any;
  const IDLE_TIMEOUT_MS = 25000;

  onMount(async () => {
    connectMessagePreview();
    connectSubtitle();

    // Get audio devices
    let res = await fetch(`http://${SERVER_URL}/audio_devices`);
    audioDevices = await res.json();

    // Select cached device
    const cachedDeviceName = localStorage.getItem('audioDevice');
    const device = audioDevices.filter(({ name }) => name === cachedDeviceName)?.[0];
    if (device) audioDevice = device;
  })

  onDestroy(() => {
    messagePreviewWs?.close();
    subtitleWs?.close();
  })

  async function connectMessagePreview() {
    messagePreviewWs?.close();
    messagePreviewWs = new WebSocket(previewMessageeUrl);
    messagePreviewWs.onmessage = (e) => {
      isLoading = false;
      messagePreviewError = false;
      try {
        const data = JSON.parse(e.data)
        if(data) {
          if (data?.status === 'done')
            onMessageStreamDone();
          else
            messagePreview = data.messages;
        }
      } catch (e) {
        messagePreview = []
      }
    }
    messagePreviewWs.onerror = (e) => {
      console.error(e)
      messagePreviewError = true;
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
          subtitles.push(`[${data.status}] ${data.role}: ${data.text}`);
          subtitles = subtitles;
          remainTasks = data.remain;
        }
      } catch (e) {
        console.log(e)
      }

      resetIdleAction();
    }
    subtitleWs.onerror = (e) => {
      console.error(e)
      subtitleError = true;
    }
  }

  async function sendMessage(message: string | null = null) {
    isLoading = true;
    const messages = message === null ? messagePreview : [...messagePreview, { role: "user", content: message }];
    await fetch(sendMessageUrl, {
      method: 'post',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: messages,
        temperature: temperature
      })
    }).then(res => {
      if (!res.ok)
        throw new Error('Failed to send message');
    }).catch(e => {
      console.error(e, messages)
      isLoading = false;
    })
  }

  async function retryMessage() {
    if (messagePreview.length <= 0) return;
    if (messagePreview[messagePreview.length-1].role === 'assistant') {
      messagePreview.splice(-1);
      messagePreview = messagePreview;
      sendMessage();
    }
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

  async function onPublishClick(lastN: number = 0) {
    if (!canPublishMessage) return;
    for (let i=0; i<messagePreview.length; i++) {
      if (lastN === 0 || i >= (messagePreview.length - lastN))
        await publishMessage(messagePreview[i]);
    }
  }

  async function publishMessage(message: {content: string, role: string}) {
    await fetch(publishMessageUrl, {
      method: 'post',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: message.role, text: message.content, device: audioDevice.id })
    }).then(res => {
      if (!res.ok)
        throw new Error('Failed to publish message');
    }).catch(e => {
      console.error(e)
    })
  }

  function deleteMessage(message: any) {
    messagePreview = messagePreview.filter((r) => r !== message);
  }

  function onMessageStreamDone() {
    if (automate) {
      onPublishClick(2);
    }
  }

  function onYtMessageSend(e: CustomEvent<YtCommentItem>) {
    messagePreview = [{ role: "user", content: e.detail.message}];
    sendMessage();
  }

  function onYtMessageAdd(e: CustomEvent<YtCommentItem>) {
    messagePreview = [...messagePreview, { role: "user", content: e.detail.message}];
    sendMessage();
  }

  function onNewYtMessage(e: CustomEvent<YtCommentItem[]>) {
    if (automate && remainTasks <= 5) {
      const _messagePreview = [...messagePreview, { role: "user", content: e.detail[0].message}];
      messagePreview = _messagePreview.slice(-1 * includeHistory);
      sendMessage();
    }
  }

  function resetIdleAction() {
    clearTimeout(idleActionTimer);
    idleActionTimer = setTimeout(() => {
      messagePreview = [];
      sendMessage('<instruction>雜談');
    }, IDLE_TIMEOUT_MS)
  }

  $: if (automate) {
    resetIdleAction();
  } else {
    clearTimeout(idleActionTimer);
  }

  function onScriptedMessageSend(e: CustomEvent<{role: string, content: string}[]>) {
    messagePreview = e.detail;
  }

  function onScriptedMessageAdd(e: CustomEvent<{role: string, content: string}[]>) {
    messagePreview = [...messagePreview, ...e.detail];
  }
</script>

<main class="pb-8">
  <div class="container w-full mt-8 lg:grid grid-cols-2 items-start gap-4">
    <div class="mb-8">
      <Tabs>
        <TabList>
          <TabHeader>YouTube</TabHeader>
          <TabHeader>Scripted</TabHeader>
        </TabList>

        <TabBody>
          <Card class="max-w-full mb-4">
            <div class="flex items-center">
              <Toggle bind:checked={automate}/>
              <Label>Automate</Label>
            </div>
          </Card>
          <YtMessages on:send={onYtMessageSend} on:add={onYtMessageAdd} on:newcomments={onNewYtMessage}/>
        </TabBody>

        <TabBody>
          <ScriptedMessages on:send={onScriptedMessageSend} on:add={onScriptedMessageAdd}/>
        </TabBody>
      </Tabs>
    </div>

    <div class="mt-0">
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
      <Card class="mt-8 max-w-full space-y-2 bg-gray-200 overflow-hidden" padding="none">
        <div class="flex items-center gap-2 p-4">
          <ButtonGroup>
            <Button size="xs" color='alternative' on:click={() => messagePreviewWs.close()}>Disconnect</Button>
            <Button size="xs" color='primary' on:click={connectMessagePreview}>Connect</Button>
          </ButtonGroup>
          <Button size="xs" class="ml-auto" color="primary" on:click={() => addEmptyMessage('user')}>Add User</Button>
          <Button size="xs" color="primary" on:click={() => addEmptyMessage('assistant')}>Add Ai</Button>
          <Button color="alternative" class="p-2" on:click={() => messagePreview = []}><Icon icon="ph:trash-bold"/></Button>
        </div>
        {#if isLoading}
          <div class="flex justify-center">
            <Spinner/>
          </div>
        {:else}
          {#if messagePreview.length <= 0}
            <div class="p-4 text-center">No messages</div>
          {/if}
          {#each messagePreview as message}
            <Card class="relative group max-w-full mx-4" padding="md">
              <div class="flex gap-2 items-center">
                <div class="flex-grow">
                  <p on:click={() => edittingMessage = message} class="text-xs font-bold text-gray-400">{message.role}</p>
                  {#if message === edittingMessage}
                    <Textarea unWrappedClass="text-base" bind:value={message.content}/>
                  {:else}
                    <p on:click={() => edittingMessage = message}>{message.content}</p>
                  {/if}
                </div>
                <div class="absolute right-2 top-2 hidden group-hover:flex gap-1">
                  {#if message === edittingMessage}
                    <button class="p-2 rounded-md bg-white border hover:bg-gray-200" on:click={() => edittingMessage = null}><Icon icon="material-symbols:close-small-rounded"/></button>
                  {:else}
            <button class="p-2 rounded-md bg-white border text-red-700 hover:bg-gray-200" on:click={() => deleteMessage(message)}><Icon icon="mdi:trash-outline"/></button>
                  {/if}
                </div>
              </div>
            </Card>
          {/each}

          <div class="p-4 w-full flex justify-center gap-2">
            <Button disabled={messagePreview.length <= 0} on:click={() => sendMessage()}>Generate</Button>
            <Button disabled={messagePreview.length <= 0} on:click={() => retryMessage()}>Retry</Button>
          </div>
        {/if}
        <div class="flex items-end gap-2 bg-white p-4">
          <Label class="flex-grow">
            Playback device
            <Select bind:value={audioDevice}>
              {#each audioDevices as device}
                <option value={device}>{device.name}</option>
              {/each}
            </Select>
          </Label>
          <Button color='primary' class="flex-grow" on:click={() => onPublishClick(2)} disabled={!canPublishMessage}>Last 2</Button>
          <Button color='primary' class="flex-grow" on:click={() => onPublishClick(0)} disabled={!canPublishMessage}>All</Button>
        </div>
      </Card>

      <!-- Subtitle display -->
      <Card class="mt-8 space-y-2 max-w-full">
        <div class="flex items-center gap-2">
          <ButtonGroup>
            <Button size="xs" color='alternative' on:click={() => subtitleWs.close()}>Disconnect</Button>
            <Button size="xs" color='primary' on:click={connectSubtitle}>Connect</Button>
          </ButtonGroup>
          <Badge>remain: {remainTasks}</Badge>
          <Button class='ml-auto p-2' color='alternative' on:click={() => subtitles = []}><Icon icon="ph:trash-bold"/></Button>
        </div>
        <ul>
          {#each subtitles.slice(-5) as subtitle}
            <li class="whitespace-pre-wrap">{subtitle}</li>
          {/each}
        </ul>
      </Card>
    </div>
  </div>
</main>

<!-- Expanded message edittor -->
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