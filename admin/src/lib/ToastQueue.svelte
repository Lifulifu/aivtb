<script lang="ts">
  import { Toast } from "flowbite-svelte";
  import { type ToastData } from "./util"
  import { fade } from "svelte/transition";
  import Icon from "@iconify/svelte";

  export let toasts: ToastData[] = []
</script>

<ol class="fixed space-y-2">
  {#each toasts as toast}
    <li transition:fade>
      <Toast color="red">
        <Icon icon="zondicons:close-outline"/>
        {toast.message}
      </Toast>
    </li>
  {/each}
</ol>

