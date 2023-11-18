<script lang="ts">
  import { Button, ButtonGroup, Card, Dropdown, DropdownItem, Input, Spinner, Toast, Modal, Textarea } from 'flowbite-svelte'
  import { onDestroy, onMount, tick } from 'svelte';
  import { fade } from 'svelte/transition';
  import { scrollToBottom } from './lib/util';
  import Icon from '@iconify/svelte';

  let aiMessage: string = '';
  let aiMessagePrefix: string = '<player>';
  let aiMessagePrefixDropdownOpen: boolean = false;
  let showAiMessageModal: boolean = false;

  type aiResponse = {q: string, a: string};
  let aiResponse: aiResponse | null = {q: '', a: ''};
  let aiResponseHandler: EventSource;
  let aiResponseError: boolean = false;
  let isLoading: boolean = false;

  let videoId: string = '';
  type YtCommentItem = {name: string, message: string, time: string}
  let ytComments: YtCommentItem[] = [];
  let ytCommentsHandler: EventSource;
  let ytCommentsDom: any = null;
  let ytCommentsError: boolean = false;
  let isAtScrollBottom: boolean = true;

  const chatUrl = 'http://localhost:8000/chat';
  const aiResponseUrl = 'http://localhost:8000/stream_response';
  const ytCommentsUrl = 'http://localhost:8000/stream_yt_comments';

  onMount(() => {
    connectAiResponse();

    if (ytCommentsDom) {
      ytCommentsDom.addEventListener("scroll", () => {
        if (
					ytCommentsDom.scrollTop + ytCommentsDom.clientHeight >=
					ytCommentsDom.scrollHeight - 2
				) {
          isAtScrollBottom = true;
        } else {
          isAtScrollBottom = false;
        }
        tick();
      })
    }
  })

  onDestroy(() => {
    aiResponseHandler.close();
    ytCommentsHandler.close();
    ytCommentsDom.removeEventListener("scroll");
  })

  $: if (ytCommentsDom && isAtScrollBottom && ytComments) autoScrollYtComments()

  async function autoScrollYtComments() {
    await tick();
    scrollToBottom(ytCommentsDom);
  }

  async function connectAiResponse() {
    if (aiResponseHandler) aiResponseHandler.close();
    aiResponseHandler = new EventSource(aiResponseUrl, { withCredentials: true });
    aiResponseHandler.onmessage = (e) => {
      isLoading = false;
      aiResponseError = false;
      try {
        const data = JSON.parse(e.data)
        if(data) aiResponse = data;
      } catch (e) {
        aiResponse = null
      }
    }
    aiResponseHandler.onerror = (e) => {
      console.error(e)
      aiResponseError = true;
    }
  }

  async function connectYtComments() {
    if (!videoId) return;
    if (ytCommentsHandler) ytCommentsHandler.close();
    ytCommentsHandler = new EventSource(`${ytCommentsUrl}?video_id=${videoId}`, { withCredentials: true });
    ytCommentsHandler.onmessage = (e) => {
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
    ytCommentsHandler.onerror = (e) => {
      console.error(e)
      ytCommentsError = true;
    }
  }

  async function sendAiMessage(prefix: string, message: string) {
    isLoading = true;
    message = encodeURI(prefix + message)
    await fetch(`${chatUrl}?message=${message}`)
  }

  function setMessagePrefix(type: string) {
    aiMessagePrefix = type;
    aiMessagePrefixDropdownOpen = false;
  }

  async function onInputSubmit() {
    await sendAiMessage(aiMessagePrefix, aiMessage);
    aiMessage = ''
  }

  async function onYtCommentClick(commentItem: YtCommentItem) {
    aiMessage = commentItem.message;
  }
</script>

<main>
  <div class="container w-full mt-8 flex gap-4">
    <!-- yt comments -->
    <Card class="min-w-[30ch] space-y-2" padding="none">
      <div class="w-full flex flex-col items-center gap-2 p-4">
        <Input bind:value={videoId}/>
        <ButtonGroup>
          <Button color='alternative' on:click={() => ytCommentsHandler.close()}>Disconnect</Button>
          <Button color='primary' on:click={connectYtComments}>Connect</Button>
        </ButtonGroup>
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
      <!-- QA streaming display -->
      <Card class="max-w-full space-y-2 bg-gray-200" padding="md">
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
        <Button on:click={connectAiResponse}>Reconnect</Button>
      </Card>

      <!-- message input -->
      <form class="mt-8 space-y-2" on:submit|preventDefault={onInputSubmit}>
        <div class="flex gap-2">
          <Button color="alternative"
            on:click={() => sendAiMessage('', '<instruction>自我介紹')}>自我介紹</Button>
          <Button color="alternative"
            on:click={() => sendAiMessage('', '<instruction>雜談')}>雜談</Button>
        </div>

        <div class="w-full">
          <ButtonGroup class="flex">
            <Button>{aiMessagePrefix === '' ? 'None' : aiMessagePrefix}</Button>
            <Dropdown bind:open={aiMessagePrefixDropdownOpen}>
              <DropdownItem on:click={() => setMessagePrefix('')}>{'None'}</DropdownItem>
              <DropdownItem on:click={() => setMessagePrefix('<player>')}>{'<player>'}</DropdownItem>
              <DropdownItem on:click={() => setMessagePrefix('<instruction>')}>{'<instruction>'}</DropdownItem>
            </Dropdown>
            <Input class="flex-grow" bind:value={aiMessage}/>
            <Button color="alternative" class="p-2" on:click={() => showAiMessageModal = true}><Icon icon="mdi:magnify-scan" height={20}/></Button>
          </ButtonGroup>
        </div>
        <Button type="submit" class="w-full" color="primary">Send</Button>
      </form>
    </div>
  </div>
</main>

<Modal bind:open={showAiMessageModal}>
  <h1>Message</h1>
  <Textarea bind:value={aiMessage}/>
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