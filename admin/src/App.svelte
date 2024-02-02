<script lang="ts">
  import { Button, ButtonGroup, Card, Input, Spinner, Toast, Modal, Textarea, NumberInput, Label, Select } from 'flowbite-svelte'
  import { Tabs, TabList, TabBody, TabHeader } from './lib/tabs/tabs';
  import { onDestroy, onMount } from 'svelte';
  import { fade } from 'svelte/transition';
  import Icon from '@iconify/svelte';

  import YtMessages from './lib/YtMessages.svelte';
  import type { YtCommentItem } from './lib/types';
  import ScriptedMessages from './lib/ScriptedMessages.svelte';

  let userQuestion: string = '';
  let showUserQuestionModal: boolean = false;
  let temperature: number = 0.7;

  let messagePreview: {role: string, content: string}[] = [];
  let messagePreviewWs: WebSocket;
  let messagePreviewError: boolean = false;
  let isLoading: boolean = false;
  $: canPublishMessage = messagePreview?.length >= 1 && messagePreview[messagePreview.length - 1].role === 'assistant';
  let edittingMessage: any = null;
  let audioDevices: {id: number, name: string}[] = [];
  let audioDevice: {id: number, name: string} = {id: -1, name: '<No device>'};

  let subtitle: string = '';
  let subtitleWs: WebSocket;
  let subtitleError: boolean = false;

  const SERVER_URL = 'localhost:8000';
  const sendMessageUrl = `http://${SERVER_URL}/send_message`;
  const publishMessageUrl = `http://${SERVER_URL}/publish_message`;
  const previewMessageeUrl = `ws://${SERVER_URL}/preview_message`;
  const subtitleUrl = `ws://${SERVER_URL}/subtitle`;

  onMount(async () => {
    connectMessagePreview();
    connectSubtitle();

    // Get audio devices
    let res = await fetch(`http://${SERVER_URL}/audio_devices`);
    audioDevices = await res.json();
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

  async function publishMessage() {
    if (!canPublishMessage) return;
    const q = messagePreview[messagePreview.length - 2]?.content ?? '';
    const a = messagePreview[messagePreview.length - 1]?.content ?? '';
    await fetch(publishMessageUrl, {
      method: 'post',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ q, a, q_device: audioDevice.id, a_device: audioDevice.id })
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

  function onYtMessageSubmit(e: CustomEvent<YtCommentItem>) {
    messagePreview = [...messagePreview, { role: "user", content: e.detail.message}];
  }

  function onScriptedMessageSubmit(e: CustomEvent<{role: string, content: string}[]>) {
    messagePreview = e.detail;
  }
</script>

<main>
  <div class="container w-full mt-8 lg:grid grid-cols-2 items-start gap-4">
    <div class="mb-8">
      <Tabs>
        <TabList>
          <TabHeader>YouTube</TabHeader>
          <TabHeader>Scripted</TabHeader>
        </TabList>

        <TabBody>
          <YtMessages on:submit={onYtMessageSubmit}/>
        </TabBody>

        <TabBody>
          <ScriptedMessages on:submit={onScriptedMessageSubmit}/>
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
                    <Textarea unWrappedClass="text-base" bind:value={message.content}/>
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
                    {:else}
                      <button class="p-2 rounded-full hover:bg-gray-200" on:click={() => sendMessage()}><Icon icon="material-symbols:arrow-forward"/></button>
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
            <Select bind:value={audioDevice}>
              {#each audioDevices as device}
                <option value={device}>{device.name}</option>
              {/each}
            </Select>
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