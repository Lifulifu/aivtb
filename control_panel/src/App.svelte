<script lang="ts">
  import {Button, Textarea} from 'flowbite-svelte'

  let inputMessage: string = ''

  async function sendMessage() {
    console.log(inputMessage);
    inputMessage = '';
  }
</script>

<main>
  <form class="container mt-8" on:submit={sendMessage}>
    <Textarea bind:value={inputMessage}/>
    <Button type="submit" class="w-full" color="primary">Send</Button>
  </form>
</main>
