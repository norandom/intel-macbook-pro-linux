// Managed by t2-mac-kde (desktop). The rabbit's screen filters in KDE (KWin effect).
//
// Hyprland runs ~/.config/hypr/shaders/night-<mode>.glsl over the finished screen
// (decoration:screen_shader). KWin has no such hook, so this effect redirects every window
// into an offscreen texture and draws it through the same filter: the deploy rewrites the
// Hyprland shaders for KWin (manage/kwin_rabbit.py) into ~/.local/share/t2-mac-kde/kwin-rabbit,
// this adds KWin's GLSL version line. The mode is ~/.local/state/hypr-nightmode (written by
// hypr-nightmode in both sessions), watched for changes: shared with Hyprland, kept across logins.
#include <effect/effecthandler.h>
#include <effect/effectwindow.h>
#include <effect/offscreeneffect.h>
#include <opengl/eglcontext.h>
#include <opengl/glshader.h>
#include <opengl/glshadermanager.h>

#include <QDir>
#include <QFile>
#include <QFileSystemWatcher>
#include <QLoggingCategory>
#include <QSet>
#include <QStandardPaths>

Q_LOGGING_CATEGORY(T2RABBIT, "t2rabbit", QtInfoMsg)

namespace KWin
{

static const QStringList MODES = {QStringLiteral("green"), QStringLiteral("dark"), QStringLiteral("grayscale"),
                                  QStringLiteral("monochrome"), QStringLiteral("warmwhite")};

class RabbitEffect : public OffscreenEffect
{
    Q_OBJECT
public:
    RabbitEffect()
    {
        const QString stateDir = QDir::homePath() + QStringLiteral("/.local/state");
        m_stateFile = stateDir + QStringLiteral("/hypr-nightmode");
        m_shaderDir = QDir::homePath() + QStringLiteral("/.local/share/t2-mac-kde/kwin-rabbit");
        QDir().mkpath(stateDir);
        // hypr-nightmode replaces the file (mv): watch the directory, not the file
        m_watcher.addPath(stateDir);
        m_watcher.addPath(m_shaderDir);
        connect(&m_watcher, &QFileSystemWatcher::directoryChanged, this, &RabbitEffect::reload);
        connect(effects, &EffectsHandler::windowAdded, this, &RabbitEffect::filterWindow);
        connect(effects, &EffectsHandler::windowDeleted, this, [this](EffectWindow *w) { m_windows.remove(w); });
        reload();
    }

    ~RabbitEffect() override { clear(); }

    static bool supported() { return effects->isOpenGLCompositing(); }
    bool isActive() const override { return m_shader != nullptr; }
    int requestedEffectChainPosition() const override { return 99; }   // after everything else

private:
    QString readMode() const
    {
        QFile f(m_stateFile);
        if (!f.open(QIODevice::ReadOnly)) {
            return QStringLiteral("off");
        }
        const QString mode = QString::fromUtf8(f.readAll()).trimmed();
        return MODES.contains(mode) ? mode : QStringLiteral("off");
    }

    QByteArray shaderSource(const QString &mode) const
    {
        QFile f(m_shaderDir + QStringLiteral("/night-") + mode + QStringLiteral(".frag"));
        return f.open(QIODevice::ReadOnly) ? f.readAll() : QByteArray();
    }

    void reload()
    {
        const QString mode = readMode();
        const QByteArray source = mode == QLatin1String("off") ? QByteArray() : shaderSource(mode);
        if (mode == m_mode && source == m_source) {
            return;
        }
        m_mode = mode;
        m_source = source;
        clear();
        if (source.isEmpty()) {
            effects->addRepaintFull();
            return;
        }
        effects->makeOpenGLContextCurrent();
        ShaderManager *manager = ShaderManager::instance();
        const ShaderTraits traits = ShaderTrait::MapTexture | ShaderTrait::Modulate;
        // the GLSL dialect KWin generates its own shaders in (glshadermanager.cpp)
        const EglContext *context = EglContext::currentContext();
        const QByteArray versionLine = !context ? QByteArray()
            : context->isOpenGLES() ? QByteArrayLiteral("#version 300 es")
                                    : QByteArrayLiteral("#version 140");
        const QByteArray fragment = versionLine + "\n" + source;
        if (versionLine.isEmpty()) {
            qCWarning(T2RABBIT) << "shader for" << mode << "not usable (GLSL" << versionLine << ")";
            return;
        }
        m_shader = manager->generateCustomShader(traits, QByteArray(), fragment);
        if (!m_shader || !m_shader->isValid()) {
            qCWarning(T2RABBIT) << "shader for" << mode << "failed to compile";
            m_shader.reset();
            return;
        }
        qCInfo(T2RABBIT) << "filter" << mode;
        const auto windows = effects->stackingOrder();
        for (EffectWindow *w : windows) {
            filterWindow(w);
        }
        effects->addRepaintFull();
    }

    void filterWindow(EffectWindow *w)
    {
        if (!m_shader || m_windows.contains(w)) {
            return;
        }
        redirect(w);
        setShader(w, m_shader.get());
        m_windows.insert(w);
    }

    void clear()
    {
        for (EffectWindow *w : std::as_const(m_windows)) {
            unredirect(w);
        }
        m_windows.clear();
        m_shader.reset();
    }

    QString m_stateFile, m_shaderDir, m_mode;
    QByteArray m_source;
    QFileSystemWatcher m_watcher;
    std::unique_ptr<GLShader> m_shader;
    QSet<EffectWindow *> m_windows;
};

} // namespace KWin

KWIN_EFFECT_FACTORY_SUPPORTED(KWin::RabbitEffect, "metadata.json", return KWin::RabbitEffect::supported();)

#include "rabbit.moc"
