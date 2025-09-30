package com.example;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

public class BaselineLambdaHandler implements RequestHandler<Map<String, Object>, Map<String, Object>> {

    // Simulate heavy initialization during cold start
    static {
        System.out.println("Cold start: Initializing baseline Lambda...");
        try {
            // Simulate loading libraries, connecting to databases, etc.
            Thread.sleep(2000); // 2-second initialization delay
            initializeResources();
            System.out.println("Cold start: Baseline initialization completed");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("Initialization interrupted", e);
        }
    }

    // Simulate resource initialization
    private static void initializeResources() {
        // Simulate heavy computation during startup
        double result = 0;
        for (int i = 0; i < 1000000; i++) {
            result += Math.sqrt(i) * Math.random();
        }
        System.out.println("Resources initialized with computation result: " + result);
    }

    @Override
    public Map<String, Object> handleRequest(Map<String, Object> event, Context context) {
        long startTime = System.currentTimeMillis();

        // Log the request
        System.out.println("Processing request: " + context.getAwsRequestId());

        // Simulate some business logic
        String result = performBusinessLogic();

        long processingTime = System.currentTimeMillis() - startTime;

        // Create response
        Map<String, Object> response = new HashMap<>();
        response.put("statusCode", 200);
        response.put("message", "Baseline Lambda processing completed");
        response.put("result", result);
        response.put("requestId", context.getAwsRequestId());
        response.put("processingTimeMs", processingTime);
        response.put("remainingTimeMs", context.getRemainingTimeInMillis());
        response.put("memoryLimitMB", context.getMemoryLimitInMB());
        response.put("timestamp", System.currentTimeMillis());

        return response;
    }

    private String performBusinessLogic() {
        // Simulate some computation
        int randomValue = ThreadLocalRandom.current().nextInt(1000, 10000);
        double calculation = Math.pow(randomValue, 2) + Math.sqrt(randomValue);

        return String.format("Computed value: %.2f from input: %d", calculation, randomValue);
    }
}
