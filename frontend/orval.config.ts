import { defineConfig } from 'orval'

export default defineConfig({
  fynd: {
    input: {
      target: './openapi.json',
    },
    output: {
      mode: 'tags-split',
      target: './src/api/endpoints.ts',
      schemas: './src/api/model',
      client: 'vue-query',
      httpClient: 'fetch',
      override: {
        mutator: {
          path: './src/lib/http.ts',
          name: 'http',
        },
      },
      mock: false,
      baseUrl: '',
      clean: true,
    },
  },
})
