<script lang="ts">
  import { Button, ButtonGroup, Card, Dropdown, DropdownItem, Input, Radio, Spinner, Textarea } from 'flowbite-svelte'
  import { onDestroy, onMount } from 'svelte';

  let inputMessage: string = '';
  let messagePrefix: string = '<player>';
  let messagePrefixDropdownOpen: boolean = false;
  let response: {q: string, a: string} = {q: '', a: ''};
  let sseHandler: EventSource;
  let isLoading: boolean = false;

  onMount(() => {
    reconnect();
  })

  onDestroy(() => {
    sseHandler.close();
  })

  async function reconnect() {
    if (sseHandler) sseHandler.close();
    sseHandler = new EventSource('http://localhost:8000/stream_response', { withCredentials: true });
    sseHandler.onmessage = (e) => {
      isLoading = false;
      try {
        const data = JSON.parse(e.data)
        if(data) response = data;
      } catch (e) {
        response = {q: 'error', a: ''}
      }
    }
  }

  async function sendMessage(message: string) {
    isLoading = true;
    message = encodeURI(messagePrefix + message)
    await fetch(`http://localhost:8000/chat?message=${message}`)
  }

  function setMessagePrefix(type: string) {
    messagePrefix = type;
    messagePrefixDropdownOpen = false;
  }

  async function onInputSubmit() {
    await sendMessage(inputMessage);
    inputMessage = ''
  }
</script>

<main>
  <div class="container mt-8 space-y-2">
    <Card class="max-w-full">
      {#if isLoading}
        <div class="flex justify-center">
          <Spinner/>
        </div>
      {:else}
        {response.q}
      {/if}
    </Card>
    <Card class="max-w-full">
      {#if isLoading}
        <div class="flex justify-center">
          <Spinner/>
        </div>
      {:else}
        {response.a}
      {/if}
    </Card>
  </div>

  <form class="container mt-8 space-y-2" on:submit|preventDefault={onInputSubmit}>
    <div class="flex gap-2">
      <Button
        on:click={() => sendMessage('<instruction>自我介紹')}>自我介紹</Button>
      <Button
        on:click={() => sendMessage('<instruction>雜談')}>雜談</Button>
      <Button class="ml-auto" on:click={reconnect}>Reconnect</Button>
    </div>

    <div class="w-full">
      <ButtonGroup class="flex">
        <Button>{messagePrefix === '' ? 'None' : messagePrefix}</Button>
        <Dropdown bind:open={messagePrefixDropdownOpen}>
          <DropdownItem on:click={() => setMessagePrefix('')}>{'None'}</DropdownItem>
          <DropdownItem on:click={() => setMessagePrefix('<player>')}>{'<player>'}</DropdownItem>
          <DropdownItem on:click={() => setMessagePrefix('<instruction>')}>{'<instruction>'}</DropdownItem>
        </Dropdown>
        <Input class="flex-grow" bind:value={inputMessage}/>
      </ButtonGroup>
    </div>
    <Button type="submit" class="w-full" color="primary">Send</Button>
  </form>
</main>
