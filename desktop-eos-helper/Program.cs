using System.Text.Json;
using System.Text.RegularExpressions;
using Epic.OnlineServices;
using Epic.OnlineServices.Auth;
using Epic.OnlineServices.Logging;
using Epic.OnlineServices.Metrics;
using Epic.OnlineServices.Platform;

var helper = new EosMetricsSession();

Console.Error.WriteLine("cws eos helper started");

while (Console.ReadLine() is { } line)
{
    HelperMessage? message;
    try
    {
        message = JsonSerializer.Deserialize<HelperMessage>(line, Json.Options);
    }
    catch (JsonException error)
    {
        Json.Write(new HelperStatus("error", "invalid_json", error.GetType().Name));
        continue;
    }

    try
    {
        if (message?.Type == "begin-session")
        {
            helper.BeginSession(message.Config, message.LauncherArgs);
            continue;
        }

        if (message?.Type == "end-session")
        {
            helper.EndSession();
            break;
        }

        Json.Write(new HelperStatus("error", "unknown_message"));
    }
    catch (HelperError error)
    {
        Json.Write(new HelperStatus("error", error.Code, error.Detail));
    }
    catch (Exception error)
    {
        Json.Write(new HelperStatus("error", "unexpected_error", Secrets.Mask(error.Message)));
    }
}

helper.Dispose();

internal sealed class EosMetricsSession : IDisposable
{
    private readonly object sync = new();
    private PlatformInterface? platform;
    private EpicAccountId? localUserId;
    private CancellationTokenSource? tickLoopStop;
    private Task? tickLoopTask;
    private bool sdkInitialized;
    private bool sessionActive;

    public void BeginSession(HelperRuntimeConfig? config, HelperLauncherArgs? launcherArgs)
    {
        if (sessionActive)
        {
            Json.Write(new HelperStatus("status", "session_active"));
            return;
        }

        ValidateBeginSessionInput(config, launcherArgs);

        try
        {
            var initializeResult = InitializeSdk();
            if (initializeResult is not Result.Success and not Result.AlreadyConfigured)
            {
                throw new HelperError("eos_initialize_failed", initializeResult.ToString());
            }

            platform = CreatePlatform(config!);
            if (platform == null)
            {
                throw new HelperError("eos_platform_create_failed");
            }

            localUserId = LoginWithExchangeCode(launcherArgs!.AuthPassword!);
            if (localUserId == null || !localUserId.IsValid())
            {
                throw new HelperError("eos_login_no_user");
            }

            BeginMetricsSession(launcherArgs.AuthLogin);
            StartTickLoop();

            sessionActive = true;
            Json.Write(new HelperStatus("status", "session_active"));
        }
        catch
        {
            StopTickLoop();
            ReleaseSdk();
            throw;
        }
    }

    public void EndSession()
    {
        StopTickLoop();

        if (platform != null && localUserId != null && sessionActive)
        {
            lock (sync)
            {
                var options = new EndPlayerSessionOptions
                {
                    AccountId = localUserId,
                };
                var result = platform.GetMetricsInterface().EndPlayerSession(ref options);
                if (result != Result.Success)
                {
                    Console.Error.WriteLine($"EOS Metrics EndPlayerSession returned {result}");
                }
            }
        }

        ReleaseSdk();
        Json.Write(new HelperStatus("status", "session_ended"));
    }

    public void Dispose()
    {
        StopTickLoop();
        ReleaseSdk();
    }

    private static void ValidateBeginSessionInput(HelperRuntimeConfig? config, HelperLauncherArgs? launcherArgs)
    {
        if (config == null)
        {
            throw new HelperError("missing_config");
        }

        var missing = new List<string>();
        if (StringTools.IsBlank(config.ProductId)) missing.Add("productId");
        if (StringTools.IsBlank(config.SandboxId)) missing.Add("sandboxId");
        if (StringTools.IsBlank(config.DeploymentId)) missing.Add("deploymentId");
        if (StringTools.IsBlank(config.ClientId)) missing.Add("clientId");
        if (StringTools.IsBlank(config.ClientSecret)) missing.Add("clientSecret");
        if (missing.Count > 0)
        {
            throw new HelperError("missing_config_fields", string.Join(",", missing));
        }

        if (launcherArgs == null || StringTools.IsBlank(launcherArgs.AuthPassword))
        {
            throw new HelperError("missing_exchange_code", "Launch from Epic Games Launcher to receive AUTH_PASSWORD.");
        }

        if (!StringTools.IsBlank(launcherArgs.AuthType)
            && !string.Equals(launcherArgs.AuthType, "exchangecode", StringComparison.OrdinalIgnoreCase))
        {
            throw new HelperError("unsupported_auth_type", launcherArgs.AuthType);
        }
    }

    private Result InitializeSdk()
    {
        var initializeOptions = new InitializeOptions
        {
            ProductName = "CultivationWorldSimulator",
            ProductVersion = "1.0.0",
        };
        var result = PlatformInterface.Initialize(ref initializeOptions);
        if (result is Result.Success or Result.AlreadyConfigured)
        {
            sdkInitialized = true;
            LoggingInterface.SetLogLevel(LogCategory.AllCategories, LogLevel.Warning);
            LoggingInterface.SetCallback((ref LogMessage message) =>
            {
                Console.Error.WriteLine($"EOS {message.Level} {message.Category}: {Secrets.Mask(message.Message)}");
            });
        }

        return result;
    }

    private PlatformInterface? CreatePlatform(HelperRuntimeConfig config)
    {
        var cacheDirectory = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "CultivationWorldSimulator",
            "EpicEOSCache"
        );
        Directory.CreateDirectory(cacheDirectory);

        var options = new WindowsOptions
        {
            ProductId = config.ProductId,
            SandboxId = config.SandboxId,
            ClientCredentials = new ClientCredentials
            {
                ClientId = config.ClientId,
                ClientSecret = config.ClientSecret,
            },
            DeploymentId = config.DeploymentId,
            CacheDirectory = cacheDirectory,
            TickBudgetInMilliseconds = 10,
            IsServer = false,
            Flags = PlatformFlags.None,
            RTCOptions = null,
        };

        return PlatformInterface.Create(ref options);
    }

    private EpicAccountId? LoginWithExchangeCode(string exchangeCode)
    {
        var auth = platform!.GetAuthInterface();
        var completion = new TaskCompletionSource<LoginCallbackInfo>(
            TaskCreationOptions.RunContinuationsAsynchronously
        );
        var options = new LoginOptions
        {
            Credentials = new Credentials
            {
                Id = null,
                Token = exchangeCode,
                Type = LoginCredentialType.ExchangeCode,
            },
            ScopeFlags = AuthScopeFlags.BasicProfile,
        };

        auth.Login(ref options, null!, (ref LoginCallbackInfo info) =>
        {
            completion.TrySetResult(info);
        });

        var deadline = DateTimeOffset.UtcNow.AddSeconds(30);
        while (!completion.Task.IsCompleted && DateTimeOffset.UtcNow < deadline)
        {
            TickOnce();
            Thread.Sleep(16);
        }

        if (!completion.Task.IsCompleted)
        {
            throw new HelperError("eos_login_timeout");
        }

        var result = completion.Task.GetAwaiter().GetResult();
        if (result.ResultCode != Result.Success)
        {
            throw new HelperError("eos_login_failed", result.ResultCode.ToString());
        }

        return result.LocalUserId;
    }

    private void BeginMetricsSession(string? authLogin)
    {
        var gameSessionId = $"cws-{DateTimeOffset.UtcNow:yyyyMMddHHmmss}-{Environment.ProcessId}";
        var displayName = StringTools.IsBlank(authLogin) ? "Cultivation World Player" : "Epic Player";
        var options = new BeginPlayerSessionOptions
        {
            AccountId = localUserId!,
            DisplayName = displayName,
            ControllerType = UserControllerType.MouseKeyboard,
            ServerIp = null,
            GameSessionId = gameSessionId,
        };

        var result = platform!.GetMetricsInterface().BeginPlayerSession(ref options);
        if (result != Result.Success)
        {
            throw new HelperError("eos_metrics_begin_failed", result.ToString());
        }
    }

    private void StartTickLoop()
    {
        StopTickLoop();
        tickLoopStop = new CancellationTokenSource();
        var token = tickLoopStop.Token;
        tickLoopTask = Task.Run(() =>
        {
            while (!token.IsCancellationRequested)
            {
                TickOnce();
                Thread.Sleep(100);
            }
        }, token);
    }

    private void StopTickLoop()
    {
        var stop = tickLoopStop;
        var task = tickLoopTask;
        tickLoopStop = null;
        tickLoopTask = null;

        if (stop == null) return;
        stop.Cancel();
        try
        {
            task?.Wait(TimeSpan.FromSeconds(2));
        }
        catch (AggregateException)
        {
        }
        finally
        {
            stop.Dispose();
        }
    }

    private void TickOnce()
    {
        var currentPlatform = platform;
        if (currentPlatform == null) return;

        lock (sync)
        {
            currentPlatform.Tick();
        }
    }

    private void ReleaseSdk()
    {
        if (platform != null)
        {
            lock (sync)
            {
                platform.Release();
                platform = null;
            }
        }

        localUserId = null;
        sessionActive = false;

        if (sdkInitialized)
        {
            var result = PlatformInterface.Shutdown();
            if (result != Result.Success)
            {
                Console.Error.WriteLine($"EOS Shutdown returned {result}");
            }
            sdkInitialized = false;
        }
    }
}

internal static class Json
{
    public static readonly JsonSerializerOptions Options = new()
    {
        PropertyNameCaseInsensitive = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
    };

    public static void Write(HelperStatus status)
    {
        Console.WriteLine(JsonSerializer.Serialize(status, Options));
        Console.Out.Flush();
    }
}

internal static class StringTools
{
    public static bool IsBlank(string? value) => string.IsNullOrWhiteSpace(value);
}

internal static class Secrets
{
    public static string Mask(string? value)
    {
        if (string.IsNullOrEmpty(value)) return string.Empty;

        var masked = Regex.Replace(
            value,
            @"(-AUTH_PASSWORD(?:=|\s+))\S+",
            "$1[redacted]",
            RegexOptions.IgnoreCase
        );
        masked = Regex.Replace(
            masked,
            @"(""clientSecret""\s*:\s*"")[^""]+("")",
            "$1[redacted]$2",
            RegexOptions.IgnoreCase
        );
        masked = Regex.Replace(
            masked,
            @"(""authPassword""\s*:\s*"")[^""]+("")",
            "$1[redacted]$2",
            RegexOptions.IgnoreCase
        );
        return masked;
    }
}

internal sealed class HelperError(string code, string? detail = null) : Exception(code)
{
    public string Code { get; } = code;
    public string? Detail { get; } = detail;
}

internal sealed class HelperMessage
{
    public string? Type { get; set; }
    public HelperRuntimeConfig? Config { get; set; }
    public HelperLauncherArgs? LauncherArgs { get; set; }
}

internal sealed class HelperRuntimeConfig
{
    public string? Environment { get; set; }
    public string? ProductId { get; set; }
    public string? SandboxId { get; set; }
    public string? DeploymentId { get; set; }
    public string? ClientId { get; set; }
    public string? ClientSecret { get; set; }
}

internal sealed class HelperLauncherArgs
{
    public string? DeploymentId { get; set; }
    public string? SandboxId { get; set; }
    public string? AuthLogin { get; set; }
    public string? AuthPassword { get; set; }
    public string? AuthType { get; set; }
}

internal sealed record HelperStatus(string Type, string State, string? Detail = null);
