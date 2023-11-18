<script lang="ts">
  import { Button, ButtonGroup, Card, Dropdown, DropdownItem, Input, Spinner, Toast, Modal, Textarea, NumberInput } from 'flowbite-svelte'
  import { onDestroy, onMount, tick } from 'svelte';
  import { fade } from 'svelte/transition';
  import { scrollToBottom } from './lib/util';
  import Icon from '@iconify/svelte';

  let userMessage: string = '';
  let userMessagePrefix: string = '<player>';
  let userMessagePrefixDropdownOpen: boolean = false;
  let showUserMessageModal: boolean = false;
  let temperature: number = 0.7;

  type aiResponse = {q: string, a: string};
  let aiResponse: aiResponse | null = {q: '', a: ''};
  let aiResponseWs: WebSocket;
  let aiResponseError: boolean = false;
  let isLoading: boolean = false;

  let videoId: string = '';
  type YtCommentItem = {name: string, message: string, time: string}
  let ytComments: YtCommentItem[] = [];
  let ytCommentsWs: WebSocket;
  let ytCommentsDom: any = null;
  let ytCommentsError: boolean = false;
  let isAtScrollBottom: boolean = true;

  const sendUserMessageUrl = 'http://localhost:8000/send_user_message';
  const aiResponseUrl = 'ws://localhost:8000/stream_ai_response';
  const ytCommentsUrl = 'ws://localhost:8000/stream_yt_comments';
  const publishAiResponseUrl = 'http://localhost:8000/publish_ai_response';

  onMount(() => {
    connectAiResponse();

    if (ytCommentsDom) {
      ytCommentsDom.addEventListener("scroll", async () => {
        if (
					ytCommentsDom.scrollTop + ytCommentsDom.clientHeight >=
					ytCommentsDom.scrollHeight - 2
				) {
          isAtScrollBottom = true;
        } else {
          isAtScrollBottom = false;
        }
        await tick();
      })
    }
  })

  onDestroy(() => {
    aiResponseWs.close();
    ytCommentsWs.close();
    ytCommentsDom.removeEventListener("scroll");
  })

  $: if (ytCommentsDom && isAtScrollBottom && ytComments) autoScrollYtComments()

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
        aiResponse = null
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

  async function sendAiMessage(prefix: string, message: string) {
    isLoading = true;
    message = encodeURI(prefix + message)
    await fetch(`${sendUserMessageUrl}?message=${message}&temperature=${temperature}`)
  }

  function setMessagePrefix(type: string) {
    userMessagePrefix = type;
    userMessagePrefixDropdownOpen = false;
  }

  async function onInputSubmit() {
    await sendAiMessage(userMessagePrefix, userMessage);
    userMessage = ''
  }

  async function onYtCommentClick(commentItem: YtCommentItem) {
    userMessage = commentItem.message;
  }

  async function publishAiResponse() {
    await fetch(publishAiResponseUrl, {
      method: 'post',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(aiResponse)
    }).catch(e => {
      console.error(e)
    })
  }
</script>

<main>
  <div class="container w-full mt-8 flex gap-4">
    <!-- yt comments -->
    <Card class="max-w-full flex-grow space-y-2" padding="none">
      <div class="w-full flex flex-col items-center gap-2 p-4">
        <Input bind:value={videoId}/>
        <div class="w-full flex gap-2">
          <ButtonGroup>
            <Button color='alternative' on:click={() => ytCommentsWs.close()}>Disconnect</Button>
            <Button color='primary' on:click={connectYtComments}>Connect</Button>
          </ButtonGroup>
          <Button class='ml-auto' color='alternative' on:click={() => ytComments = []}>Clear</Button>
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

    <div class="flex-grow">
    <!-- user message input -->
      <form class="space-y-2" on:submit|preventDefault={onInputSubmit}>
        <div class="flex gap-2">
          <Button color="alternative"
            on:click={() => sendAiMessage('', '<instruction>自我介紹')}>自我介紹</Button>
          <Button color="alternative"
            on:click={() => sendAiMessage('', '<instruction>雜談')}>雜談</Button>
        </div>

        <div class="w-full">
          <ButtonGroup class="flex">
            <Button>{userMessagePrefix === '' ? 'None' : userMessagePrefix}</Button>
            <Dropdown bind:open={userMessagePrefixDropdownOpen}>
              <DropdownItem on:click={() => setMessagePrefix('')}>{'None'}</DropdownItem>
              <DropdownItem on:click={() => setMessagePrefix('<player>')}>{'<player>'}</DropdownItem>
              <DropdownItem on:click={() => setMessagePrefix('<instruction>')}>{'<instruction>'}</DropdownItem>
            </Dropdown>
            <Input class="flex-grow" bind:value={userMessage}/>
            <Button color="alternative" class="p-2" on:click={() => showUserMessageModal = true}>
              <Icon icon="mdi:magnify-scan" height={20}/>
            </Button>
          </ButtonGroup>
        </div>
        <div class="flex gap-2 w-full">
          <NumberInput class="w-0 flex-grow" bind:value={temperature} min={0.1} max={2.0} step={0.1}/>
          <Button type="submit" class="flex-grow" color="primary">Send</Button>
        </div>
      </form>

      <!-- QA streaming display -->
      <Card class="mt-8 max-w-full space-y-2 bg-gray-200" padding="md">
        <Card class="max-w-full">
          {#if isLoading || !aiResponse}
            <div class="flex justify-center">
              <Spinner/>
            </div>
          {:else}
            {aiResponse.q}
          {/if}
        </Card>
        <Card class="max-w-full">
          {#if isLoading || !aiResponse}
            <div class="flex justify-center">
              <Spinner/>
            </div>
          {:else}
            {aiResponse.a}
          {/if}
        </Card>
        <div class="flex">
          <ButtonGroup>
            <Button color='alternative' on:click={() => aiResponseWs.close()}>Disconnect</Button>
            <Button color='primary' on:click={connectAiResponse}>Connect</Button>
          </ButtonGroup>
          <Button class='ml-auto' color='primary' on:click={publishAiResponse}>Publish</Button>
        </div>
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