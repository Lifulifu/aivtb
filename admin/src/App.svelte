<script lang="ts">
  import { Button, ButtonGroup, Card, Dropdown, DropdownItem, Input, Spinner, Toast, Modal, Textarea, NumberInput, Label, Toggle } from 'flowbite-svelte'
  import { onDestroy, onMount, tick } from 'svelte';
  import { fade } from 'svelte/transition';
  import { scrollToBottom } from './lib/util';
  import Icon from '@iconify/svelte';

  let userMessage: string = '';
  let showUserMessageModal: boolean = false;
  let temperature: number = 0.7;

  let aiResponse: {role: string, content: string}[] = [];
  let aiResponseWs: WebSocket;
  let aiResponseError: boolean = false;
  let isLoading: boolean = false;
  let playbackDeviceId: number = -1;
  $: canPublishAiResponse = aiResponse?.length >= 1;
  let edittingAiResponse: any = null;

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

  const sendUserMessageUrl = 'http://localhost:8000/send_user_message';
  const publishAiResponseUrl = 'http://localhost:8000/publish_ai_response';
  const aiResponseUrl = 'ws://localhost:8000/stream_ai_response';
  const ytCommentsUrl = 'ws://localhost:8000/stream_yt_comments';
  const subtitleUrl = 'ws://localhost:8000/stream_subtitle';
  $: console.log(aiResponse)

  onMount(() => {
    connectAiResponse();
    connectSubtitle();
  })

  onDestroy(() => {
    aiResponseWs.close();
    ytCommentsWs.close();
  })

  $: if (ytCommentsDom && autoScroll && ytComments) autoScrollYtComments()

  async function autoScrollYtComments() {
    await tick();
    scrollToBottom(ytCommentsDom);
  }

  async function connectAiResponse() {
    if (aiResponseWs) aiResponseWs.close();
    aiResponseWs = new WebSocket(aiResponseUrl);
    aiResponseWs.onmessage = (e) => {
      isLoading = false;
      aiResponseError = false;
      try {
        const data = JSON.parse(e.data)
        if(data) aiResponse = data;
      } catch (e) {
        aiResponse = []
      }
    }
    aiResponseWs.onerror = (e) => {
      console.error(e)
      aiResponseError = true;
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

  async function sendAiMessage(message: string = '') {
    isLoading = true;
    const messages = message ? [...aiResponse, { role: "user", content: message }] : aiResponse;
    await fetch(sendUserMessageUrl, {
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

  function addEmptyAiResponse(role: 'assistant'|'user' = 'assistant') {
    const message = {role, content: ''};
    edittingAiResponse = message;
    aiResponse = [...aiResponse, message];
  }

  async function onInputSubmit() {
    await sendAiMessage(userMessage);
    userMessage = ''
  }

  async function onInputClearAndSend() {
    aiResponse = [];
    await sendAiMessage(userMessage);
    userMessage = '';
  }

  async function onYtCommentClick(commentItem: YtCommentItem) {
    userMessage = commentItem.message;
  }

  async function publishAiResponse() {
    if (!canPublishAiResponse) return;
    const q = aiResponse[aiResponse.length - 2].content;
    const a = aiResponse[aiResponse.length - 1].content;
    // only read if it is a user question
    await fetch(publishAiResponseUrl, {
      method: 'post',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ q, a, device: playbackDeviceId })
    }).catch(e => {
      console.error(e)
    })
  }

  function deleteAiResponse(response: any) {
    aiResponse = aiResponse.filter((r) => r !== response);
  }

  function regenerateAiResponse(response: any) {
    const _aiResponse = []
    // delete all messages after response
    for(let res of aiResponse) {
      if (res === response) break;
      _aiResponse.push(res);
    }
    aiResponse = _aiResponse;
    sendAiMessage();
  }
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
            on:click={() => sendAiMessage('<instruction>自我介紹')}>自我介紹</Button>
          <Button color="alternative"
            on:click={() => sendAiMessage('<instruction>雜談')}>雜談</Button>
          <Button color="alternative"
            on:click={() => sendAiMessage('<instruction>繼續')}>繼續</Button>
        </div>

        <div class="w-full flex gap-2">
          <Input class="flex-grow" bind:value={userMessage}/>
          <Button color="alternative" class="p-2" on:click={() => showUserMessageModal = true}>
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
            <Button color='alternative' on:click={() => aiResponseWs.close()}>Disconnect</Button>
            <Button color='primary' on:click={connectAiResponse}>Connect</Button>
          </ButtonGroup>
          <Button class="ml-auto" color="primary" on:click={() => addEmptyAiResponse('user')}>Add User</Button>
          <Button color="primary" on:click={() => addEmptyAiResponse('assistant')}>Add Ai</Button>
          <Button color="alternative" on:click={() => aiResponse = []}>Clear</Button>
        </div>
        {#if isLoading}
          <div class="flex justify-center">
            <Spinner/>
          </div>
        {:else}
          {#each aiResponse as res}
            <Card class="max-w-full" padding="md">
              <div class="flex gap-2 items-center">
                <div class="flex-grow">
                  <p on:click={() => edittingAiResponse = res} class="text-xs font-bold text-gray-400">{res.role}</p>
                  {#if res === edittingAiResponse}
                    <Textarea class="mr-2 text-lg" bind:value={res.content}/>
                  {:else}
                    <p on:click={() => edittingAiResponse = res}>{res.content}</p>
                  {/if}
                </div>
                <div class="flex">
                  {#if res === edittingAiResponse}
                    <button class="p-2 rounded-full hover:bg-gray-200" on:click={() => edittingAiResponse = null}><Icon icon="material-symbols:close-small-rounded"/></button>
                  {:else}
                    {#if res.role === 'assistant'}
                      <button class="p-2 rounded-full hover:bg-gray-200" on:click={() => regenerateAiResponse(res)}><Icon icon="material-symbols:refresh-rounded"/></button>
                    {/if}
                    <button class="p-2 text-red-700 rounded-full hover:bg-gray-200" on:click={() => deleteAiResponse(res)}><Icon icon="mdi:trash-outline"/></button>
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
          <Button color='primary' class="flex-grow" on:click={publishAiResponse} disabled={!canPublishAiResponse}>Publish</Button>
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

<Modal bind:open={showUserMessageModal}>
  <h1>Message</h1>
  <Textarea bind:value={userMessage}/>
</Modal>

{#if aiResponseError}
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